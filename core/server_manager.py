"""
Модуль для управления Minecraft серверами.
Поддерживает: получение пинга, MOTD, иконку сервера.
"""

import asyncio
import json
import socket
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerInfo:
    """Информация о сервере."""
    name: str
    host: str
    port: int
    ip: str
    icon_path: Optional[str] = None

    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON."""
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "ip": self.ip,
            "icon_path": self.icon_path
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServerInfo":
        """Создание из словаря."""
        return cls(
            name=data["name"],
            host=data["host"],
            port=data["port"],
            ip=data["ip"],
            icon_path=data.get("icon_path")
        )


class ServerManager:
    """Менеджер серверов для управления списком серверов."""

    def __init__(self, config_path: str = "data/servers.json"):
        self.config_path = config_path
        self.servers: list[ServerInfo] = []
        self._load_servers()

    def _load_servers(self) -> None:
        """Загрузка серверов из файла."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.servers = [ServerInfo.from_dict(s) for s in data]
        except FileNotFoundError:
            self.servers = []
        except json.JSONDecodeError:
            self.servers = []

    def _save_servers(self) -> None:
        """Сохранение серверов в файл."""
        import os
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self.servers], f, ensure_ascii=False, indent=2)

    def add_server(self, name: str, host: str, port: int = 25565) -> ServerInfo:
        """Добавление сервера в список."""
        server = ServerInfo(name=name, host=host, port=port, ip=f"{host}:{port}")
        self.servers.append(server)
        self._save_servers()
        return server

    def remove_server(self, server: ServerInfo) -> None:
        """Удаление сервера из списка."""
        self.servers.remove(server)
        self._save_servers()

    def get_server(self, name: str) -> Optional[ServerInfo]:
        """Получение сервера по имени."""
        for server in self.servers:
            if server.name == name:
                return server
        return None

    def get_all_servers(self) -> list[ServerInfo]:
        """Получение всех серверов."""
        return self.servers.copy()

    async def get_server_motd(
        self, host: str, port: int = 25565, timeout: int = 5
    ) -> Optional[dict]:
        """
        Получение MOTD (Message of the Day) сервера.
        Возвращает словарь с описанием сервера или None при ошибке.
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )

            # Отправляем запрос status (Minecraft protocol)
            packet = (
                bytes([0x00]) +  # Пакет status request
                bytes([0x00]) +  # Версия протокола
                self._encode_string(host) +
                port.to_bytes(2, "big") +
                bytes([0x01])  # Тип запроса
            )

            writer.write(packet)
            await writer.drain()

            # Читаем ответ
            length_bytes = await reader.read(1)
            if not length_bytes:
                writer.close()
                await writer.wait_closed()
                return None

            length = length_bytes[0]
            response = await reader.read(length)

            writer.close()
            await writer.wait_closed()

            data = json.loads(response.decode("utf-8"))
            return data.get("data")

        except (asyncio.TimeoutError, OSError, socket.timeout):
            return None

    async def get_server_ping(
        self, host: str, port: int = 25565, timeout: int = 5
    ) -> Optional[int]:
        """
        Получение пинга сервера в миллисекундах.
        Возвращает int или None при ошибке.
        """
        try:
            start_time = asyncio.get_event_loop().time()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            end_time = asyncio.get_event_loop().time()

            writer.close()
            await writer.wait_closed()

            ping_ms = int((end_time - start_time) * 1000)
            return ping_ms

        except (asyncio.TimeoutError, OSError, socket.timeout):
            return None

    def _encode_string(self, s: str) -> bytes:
        """Кодирование строки в формат Minecraft."""
        encoded = s.encode("utf-8")
        return bytes([len(encoded)]) + encoded

    async def refresh_server_info(self, server: ServerInfo) -> dict:
        """
        Обновление информации о сервере (MOTD, пинг).
        Возвращает словарь с информацией.
        """
        motd = await self.get_server_motd(server.host, server.port)
        ping = await self.get_server_ping(server.host, server.port)

        return {
            "server": server,
            "motd": motd,
            "ping": ping,
            "online": motd is not None
        }


# Пример использования:
# if __name__ == "__main__":
#     manager = ServerManager()
#     manager.add_server("Hypixel", "mc.hypixel.net", 25565)
#
#     async def main():
#         info = await manager.refresh_server_info(manager.servers[0])
#         print(f"Сервер: {info['server'].name}")
#         print(f"Пинг: {info['ping']} мс")
#         print(f"Онлайн: {info['online']}")
#
#     asyncio.run(main())
