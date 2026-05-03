"""Конфигурация приложения."""

import json
from dataclasses import asdict, dataclass

from typing_extensions import Self

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
    # Microsoft OAuth
    ms_client_id: str = ""
    ms_refresh_token: str = ""

    @classmethod
    def load(cls) -> Self:
        """Загружает конфигурацию из файла."""
        config_path = get_config_dir() / "config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
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
