"""Пинг Minecraft серверов (Status Protocol)."""

import asyncio
import json
import struct
from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class ServerStatus:
    """Ответ от Minecraft сервера."""

    host: str
    port: int
    online: bool
    ping_ms: float = -1.0
    motd: str = ""
    players_online: int = 0
    players_max: int = 0
    version: str = ""
    favicon: str = ""
    error: str = ""


def _pack_varint(value: int) -> bytes:
    """Упаковывает int в Minecraft VarInt."""
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            result.append(byte | 0x80)
        else:
            result.append(byte)
            break
    return bytes(result)


def _unpack_varint(data: bytes, offset: int = 0) -> tuple[int, int]:
    """Распаковывает Minecraft VarInt. Возвращает (value, new_offset)."""
    value = 0
    shift = 0
    while True:
        byte = data[offset]
        value |= (byte & 0x7F) << shift
        offset += 1
        if not (byte & 0x80):
            break
        shift += 7
        if shift >= 35:
            raise ValueError("VarInt слишком большой")
    return value, offset


def _encode_packet(packet_id: int, data: bytes = b"") -> bytes:
    """Кодирует пакет Minecraft."""
    payload = _pack_varint(packet_id) + data
    return _pack_varint(len(payload)) + payload


async def _read_varint_from_stream(reader: asyncio.StreamReader) -> int:  # type: ignore[return]
    """Читает VarInt из потока."""
    value = 0
    shift = 0
    while True:
        chunk = await reader.read(1)
        if not chunk:
            raise ConnectionError("Поток закрыт при чтении VarInt")
        byte = struct.unpack("B", chunk)[0]
        value |= (byte & 0x7F) << shift
        shift += 7
        if not (byte & 0x80):
            break
    return value


async def ping_server(host: str, port: int = 25565, timeout: float = 5.0) -> ServerStatus:
    """Пингует Minecraft сервер и возвращает статус.

    Реализован базовый Handshake + Status Request протокол.
    """
    start_time = asyncio.get_event_loop().time()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )

        # Handshake
        handshake_data = (
            _pack_varint(760)  # protocol version (1.19.2 ≈ 760, сервер обычно не проверяет строго)
            + _pack_varint(len(host.encode("utf-8"))) + host.encode("utf-8")
            + struct.pack(">H", port)
            + _pack_varint(1)  # next state = status
        )
        writer.write(_encode_packet(0, handshake_data))

        # Status Request
        writer.write(_encode_packet(0))
        await writer.drain()

        # Читаем длину пакета
        length = await _read_varint_from_stream(reader)
        packet_data = await asyncio.wait_for(reader.read(length), timeout=timeout)

        # Парсим пакет
        pkt_id, offset = _unpack_varint(packet_data)
        if pkt_id != 0:
            raise ValueError(f"Неожиданный packet ID: {pkt_id}")

        json_len, offset = _unpack_varint(packet_data, offset)
        json_str = packet_data[offset : offset + json_len].decode("utf-8")
        response: dict[str, Any] = json.loads(json_str)

        # Ping
        ping_payload = struct.pack(">Q", int(start_time * 1000))
        writer.write(_encode_packet(1, ping_payload))
        await writer.drain()

        ping_length = await _read_varint_from_stream(reader)
        await asyncio.wait_for(reader.read(ping_length), timeout=timeout)
        ping_ms = (asyncio.get_event_loop().time() - start_time) * 1000

        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

        # Парсим MOTD
        motd_raw = response.get("description", {})
        if isinstance(motd_raw, dict):
            motd = motd_raw.get("text", "")
        else:
            motd = str(motd_raw)

        players = response.get("players", {})
        version_info = response.get("version", {})

        return ServerStatus(
            host=host,
            port=port,
            online=True,
            ping_ms=round(ping_ms, 1),
            motd=motd,
            players_online=players.get("online", 0),
            players_max=players.get("max", 0),
            version=version_info.get("name", ""),
            favicon=response.get("favicon", ""),
        )
    except asyncio.TimeoutError:
        logger.debug("Таймаут пинга {}:{}", host, port)
        return ServerStatus(host=host, port=port, online=False, error="Таймаут")
    except OSError as exc:
        logger.debug("Ошибка соединения {}:{} — {}", host, port, exc)
        return ServerStatus(host=host, port=port, online=False, error=str(exc))
    except Exception as exc:
        logger.debug("Ошибка пинга {}:{} — {}", host, port, exc)
        return ServerStatus(host=host, port=port, online=False, error=str(exc))
