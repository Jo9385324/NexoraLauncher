"""Конфигурация приложения."""

import json
from dataclasses import asdict, dataclass, field

from typing_extensions import Self

from quantumlauncher.utils.crypto import TokenVault
from quantumlauncher.utils.paths import get_config_dir


@dataclass
class AppConfig:
    """Конфигурация QuantumLauncher."""

    appearance_mode: str = "dark"
    color_theme: str = "blue"
    window_width: int = 1200
    window_height: int = 800
    java_path: str = ""
    max_memory: int = 4096
    min_memory: int = 512
    jvm_profile: str = "default"
    fullscreen: bool = False
    last_username: str = ""
    last_version: str = ""
    language: str = "ru"
    # Microsoft OAuth (хранятся в зашифрованном виде)
    _ms_client_id: str = field(default="", repr=False)
    _ms_refresh_token: str = field(default="", repr=False)

    # CurseForge API ключ (зашифрованный)
    _curseforge_api_key: str = field(default="", repr=False)

    # Версия схемы для будущих миграций
    _schema_version: int = 1

    def __post_init__(self) -> None:
        """Валидация значений после создания."""
        valid_appearance = ("dark", "light")
        self.appearance_mode = (
            self.appearance_mode if self.appearance_mode in valid_appearance else "dark"
        )
        valid_themes = ("blue", "green", "dark-blue")
        self.color_theme = (
            self.color_theme if self.color_theme in valid_themes else "blue"
        )
        self.window_width = max(800, min(3840, self.window_width))
        self.window_height = max(600, min(2160, self.window_height))
        self.max_memory = max(512, min(65536, self.max_memory))
        self.min_memory = max(256, min(self.max_memory, self.min_memory))
        valid_profiles = ("default", "performance", "low")
        self.jvm_profile = (
            self.jvm_profile if self.jvm_profile in valid_profiles else "default"
        )
        self.language = self.language if self.language in ("ru", "en") else "ru"

    @property
    def ms_client_id(self) -> str:
        return TokenVault.decrypt(self._ms_client_id)

    @ms_client_id.setter
    def ms_client_id(self, value: str) -> None:
        self._ms_client_id = TokenVault.encrypt(value)

    @property
    def ms_refresh_token(self) -> str:
        return TokenVault.decrypt(self._ms_refresh_token)

    @ms_refresh_token.setter
    def ms_refresh_token(self, value: str) -> None:
        self._ms_refresh_token = TokenVault.encrypt(value)

    @property
    def curseforge_api_key(self) -> str:
        return TokenVault.decrypt(self._curseforge_api_key)

    @curseforge_api_key.setter
    def curseforge_api_key(self, value: str) -> None:
        self._curseforge_api_key = TokenVault.encrypt(value)

    @classmethod
    def load(cls) -> Self:
        """Загружает конфигурацию из файла."""
        config_path = get_config_dir() / "config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                # Поддержка старых незашифрованных конфигов
                if "ms_client_id" in data and "_ms_client_id" not in data:
                    data["_ms_client_id"] = TokenVault.encrypt(data.pop("ms_client_id", ""))
                if "ms_refresh_token" in data and "_ms_refresh_token" not in data:
                    data["_ms_refresh_token"] = TokenVault.encrypt(data.pop("ms_refresh_token", ""))
                if "curseforge_api_key" in data and "_curseforge_api_key" not in data:
                    data["_curseforge_api_key"] = TokenVault.encrypt(
                        data.pop("curseforge_api_key", "")
                    )
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()

    def save(self) -> None:
        """Сохраняет конфигурацию в файл."""
        config_path = get_config_dir() / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
