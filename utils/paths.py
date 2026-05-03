"""Управление путями и директориями."""

from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir, user_data_dir

APP_NAME = "QuantumLauncher"
APP_AUTHOR = "QuantumLauncher"


def get_data_dir() -> Path:
    """Директория данных приложения."""
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def get_config_dir() -> Path:
    """Директория конфигурации."""
    return Path(user_config_dir(APP_NAME, APP_AUTHOR))


def get_cache_dir() -> Path:
    """Директория кэша."""
    return Path(user_cache_dir(APP_NAME, APP_AUTHOR))


def get_logs_dir() -> Path:
    """Директория логов."""
    return get_data_dir() / "logs"


def get_instances_dir() -> Path:
    """Директория инстансов Minecraft."""
    return get_data_dir() / "instances"


def get_versions_dir() -> Path:
    """Директория версий Minecraft."""
    return get_data_dir() / "versions"


def get_assets_dir() -> Path:
    """Директория ассетов."""
    return get_data_dir() / "assets"


def get_libraries_dir() -> Path:
    """Директория библиотек."""
    return get_data_dir() / "libraries"


def ensure_directories() -> None:
    """Создаёт все необходимые директории."""
    dirs = [
        get_data_dir(),
        get_config_dir(),
        get_cache_dir(),
        get_logs_dir(),
        get_instances_dir(),
        get_versions_dir(),
        get_assets_dir(),
        get_libraries_dir(),
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
