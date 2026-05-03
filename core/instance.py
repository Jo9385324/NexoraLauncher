"""Управление инстансами Minecraft (сборками)."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Self

from loguru import logger

from quantumlauncher.utils.paths import get_instances_dir


@dataclass
class Instance:
    """Инстанс Minecraft — изолированная сборка."""

    name: str
    version: str
    mod_loader: str = "vanilla"  # vanilla | forge | fabric | quilt
    loader_version: str = ""
    java_path: str = ""
    max_memory: int = 4096
    min_memory: int = 512
    width: int = 1280
    height: int = 720
    fullscreen: bool = False
    mods: list[str] | None = None
    created_at: str = ""
    last_played: str = ""
    play_count: int = 0

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if self.mods is None:
            self.mods = []

    @property
    def path(self) -> Path:
        """Путь к директории инстанса."""
        return get_instances_dir() / self.name

    @property
    def game_dir(self) -> Path:
        """Путь к .minecraft внутри инстанса."""
        return self.path / ".minecraft"

    @property
    def mods_dir(self) -> Path:
        """Путь к папке модов."""
        return self.game_dir / "mods"

    def ensure_dirs(self) -> None:
        """Создаёт необходимые директории."""
        self.game_dir.mkdir(parents=True, exist_ok=True)
        self.mods_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        """Сериализует в dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Десериализует из dict."""
        # Фильтруем только известные поля
        fields = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in fields}
        return cls(**filtered)

    def save(self) -> None:
        """Сохраняет инстанс в JSON."""
        self.ensure_dirs()
        config_path = self.path / "instance.json"
        config_path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.debug("Инстанс '{}' сохранён", self.name)

    @classmethod
    def load(cls, name: str) -> Self | None:
        """Загружает инстанс по имени."""
        config_path = get_instances_dir() / name / "instance.json"
        if not config_path.exists():
            return None
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Ошибка загрузки инстанса '{}': {}", name, e)
            return None

    def on_launch(self) -> None:
        """Обновляет статистику при запуске."""
        self.last_played = datetime.now().isoformat()
        self.play_count += 1
        self.save()


class InstanceManager:
    """Менеджер всех инстансов."""

    @staticmethod
    def list_instances() -> list[Instance]:
        """Возвращает список всех инстансов."""
        instances_dir = get_instances_dir()
        if not instances_dir.exists():
            return []

        instances = []
        for path in instances_dir.iterdir():
            if path.is_dir():
                instance = Instance.load(path.name)
                if instance:
                    instances.append(instance)
        return instances

    @staticmethod
    def create(name: str, version: str, mod_loader: str = "vanilla") -> Instance:
        """Создаёт новый инстанс."""
        instance = Instance(name=name, version=version, mod_loader=mod_loader)
        instance.save()
        logger.info("Создан инстанс '{}' ({} {})", name, mod_loader, version)
        return instance

    @staticmethod
    def delete(name: str) -> bool:
        """Удаляет инстанс."""
        import shutil

        path = get_instances_dir() / name
        if not path.exists():
            return False
        shutil.rmtree(path)
        logger.info("Инстанс '{}' удалён", name)
        return True
