"""Discord Rich Presence интеграция."""

import time
from typing import Any

from loguru import logger


class DiscordRPC:
    """Управляет Discord Rich Presence статусом."""

    CLIENT_ID = "1234567890123456789"  # placeholder — нужен реальный ID приложения

    def __init__(self) -> None:
        self._rpc: Any | None = None
        self._connected = False

    def connect(self) -> bool:
        """Подключается к Discord. Возвращает True если успешно."""
        if self._connected:
            return True
        try:
            from pypresence import Presence

            self._rpc = Presence(self.CLIENT_ID)
            self._rpc.connect()
            self._connected = True
            logger.info("Discord RPC подключён")
            return True
        except Exception as exc:
            logger.debug("Discord RPC недоступен: {}", exc)
            self._rpc = None
            self._connected = False
            return False

    def update_launcher(self) -> None:
        """Показывает статус 'В лаунчере'."""
        if not self._connected or self._rpc is None:
            return
        try:
            self._rpc.update(
                state="В лаунчере",
                details="QuantumLauncher",
                large_image="launcher",
                large_text="QuantumLauncher",
                start=int(time.time()),
            )
        except Exception as exc:
            logger.debug("Ошибка обновления Discord RPC: {}", exc)
            self._connected = False

    def update_playing(self, version: str, mod_loader: str = "") -> None:
        """Показывает статус 'Играет в Minecraft'."""
        if not self._connected or self._rpc is None:
            return
        try:
            details = f"Minecraft {version}"
            if mod_loader and mod_loader != "vanilla":
                state = f"({mod_loader.capitalize()})"
            else:
                state = "Vanilla"

            self._rpc.update(
                state=state,
                details=details,
                large_image="minecraft",
                large_text=f"Minecraft {version}",
                small_image="launcher",
                small_text="QuantumLauncher",
                start=int(time.time()),
            )
        except Exception as exc:
            logger.debug("Ошибка обновления Discord RPC: {}", exc)
            self._connected = False

    def clear(self) -> None:
        """Очищает статус."""
        if not self._connected or self._rpc is None:
            return
        try:
            self._rpc.clear()
        except Exception as exc:
            logger.debug("Ошибка очистки Discord RPC: {}", exc)
            self._connected = False

    def close(self) -> None:
        """Закрывает соединение."""
        if self._rpc is not None:
            try:
                self._rpc.close()
            except Exception as exc:
                logger.debug("Ошибка закрытия Discord RPC: {}", exc)
        self._rpc = None
        self._connected = False
