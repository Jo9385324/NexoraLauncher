"""Точка входа в QuantumLauncher."""

import sys
from pathlib import Path

# При прямом запуске main.py добавляем корень проекта в sys.path
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

import customtkinter as ctk
from loguru import logger

from quantumlauncher.ui.main_window import MainWindow
from quantumlauncher.utils.config import AppConfig
from quantumlauncher.utils.paths import ensure_directories


def setup_logging() -> None:
    """Настройка логирования."""
    from quantumlauncher.utils.paths import get_logs_dir

    logs_dir = get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, level="INFO", format=fmt)
    logger.add(
        logs_dir / "launcher.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        encoding="utf-8",
    )


def main() -> None:
    """Главная функция запуска лаунчера."""
    setup_logging()
    logger.info("QuantumLauncher v{} запускается...", __import__("quantumlauncher").__version__)

    ensure_directories()
    config = AppConfig.load()

    ctk.set_appearance_mode(config.appearance_mode)
    ctk.set_default_color_theme(config.color_theme)

    app = MainWindow()
    app.mainloop()

    logger.info("QuantumLauncher завершил работу.")


if __name__ == "__main__":
    main()
