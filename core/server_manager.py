"""
Модуль для управления Minecraft серверами.
Поддерживает: получение пинга, MOTD, иконку сервера.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger

from quantumlauncher.core.server_ping import ServerStatus, ping_server
from quantumlauncher.utils.paths import get_data_dir


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
            "icon_path": self.icon_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServerInfo":
        """Создание из словаря."""
        return cls(
            name=data["name"],
            host=data["host"],
            port=data["port"],
            ip=data["ip"],
            icon_path=data.get("icon_path"),
        )


class ServerManager:
    """Менеджер серверов для управления списком серверов."""

    def __init__(self, config_path: str | None = None) -> None:
        if config_path is None:
            config_path = str(get_data_dir() / "servers.json")
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
            logger.warning("Файл серверов повреждён, создаём новый")
            self.servers = []

    def _save_servers(self) -> None:
        """Сохранение серверов в файл."""
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump([s.to_dict() for s in self.servers], f, ensure_ascii=False, indent=2)

    def add_server(self, name: str, host: str, port: int = 25565) -> ServerInfo:
        """Добавление сервера в список."""
        server = ServerInfo(name=name, host=host, port=port, ip=f"{host}:{port}")
        self.servers.append(server)
        self._save_servers()
        logger.info("Добавлен сервер {} ({}:{})", name, host, port)
        return server

    def remove_server(self, server: ServerInfo) -> None:
        """Удаление сервера из списка."""
        self.servers.remove(server)
        self._save_servers()
        logger.info("Удалён сервер {}", server.name)

    def get_server(self, name: str) -> Optional[ServerInfo]:
        """Получение сервера по имени."""
        for srv in self.servers:
            if srv.name == name:
                return srv
        return None

    def get_all_servers(self) -> list[ServerInfo]:
        """Получение всех серверов."""
        return self.servers.copy()

    async def refresh_server_info(self, server: ServerInfo) -> ServerStatus:
        """Обновление информации о сервере (MOTD, пинг).

        Использует корректную реализацию Minecraft Server List Ping.
        """
        return await ping_server(server.host, server.port, timeout=5.0)
