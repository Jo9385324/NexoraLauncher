"""Автоматическая загрузка и установка Java (Eclipse Adoptium)."""

import os
import platform
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from loguru import logger

from quantumlauncher.utils.paths import get_data_dir

ADOPTIUM_API = "https://api.adoptium.net/v3/assets/latest"


@dataclass
class JavaDownloadInfo:
    """Информация о загружаемой Java."""

    version: int
    download_url: str
    checksum: str
    size: int
    filename: str


def _get_os_arch() -> tuple[str, str]:
    """Возвращает (os, arch) для Adoptium API."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_map = {"windows": "windows", "linux": "linux", "darwin": "mac"}
    arch_map = {
        "amd64": "x64",
        "x86_64": "x64",
        "i386": "x86",
        "i686": "x86",
        "arm64": "aarch64",
        "aarch64": "aarch64",
    }

    return os_map.get(system, system), arch_map.get(machine, machine)


def fetch_java_releases(major_version: int = 21) -> list[JavaDownloadInfo]:
    """Получает список доступных релизов Java с Adoptium."""
    os_name, arch = _get_os_arch()
    url = (
        f"{ADOPTIUM_API}/{major_version}/hotspot"
        f"?vendor=eclipse&os={os_name}&architecture={arch}&image_type=jre"
    )
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()

        results: list[JavaDownloadInfo] = []
        for item in data:
            binary = item.get("binary", {})
            pkg = binary.get("package", {})
            if not pkg.get("link"):
                continue
            results.append(
                JavaDownloadInfo(
                    version=item.get("version", {}).get("major", major_version),
                    download_url=pkg["link"],
                    checksum=pkg.get("checksum", ""),
                    size=pkg.get("size", 0),
                    filename=pkg.get("name", "java.zip"),
                )
            )
        return results
    except Exception as exc:
        logger.error("Ошибка получения релизов Java: {}", exc)
        return []


def install_java(download_url: str, dest_dir: Path | None = None) -> Path | None:
    """Скачивает и распаковывает Java в директорию данных лаунчера.

    Returns:
        Путь к bin/java или None при ошибке.
    """
    if dest_dir is None:
        dest_dir = get_data_dir() / "java"
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = download_url.split("/")[-1]
    archive_path = dest_dir / filename

    try:
        logger.info("Скачивание Java: {}", download_url)
        with requests.get(download_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(archive_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        extract_dir = dest_dir / filename.replace(".zip", "").replace(".tar.gz", "")
        extract_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Распаковка Java в {}", extract_dir)
        if filename.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(extract_dir)
        elif filename.endswith(".tar.gz"):
            import tarfile

            with tarfile.open(archive_path, "r:gz") as t:
                t.extractall(extract_dir)
        else:
            logger.warning("Неизвестный формат архива: {}", filename)
            return None

        # Ищем java внутри распакованного
        java_exe = "java.exe" if platform.system() == "Windows" else "java"
        for root, _dirs, files in os.walk(extract_dir):
            if java_exe in files:
                java_path = Path(root) / java_exe
                logger.info("Java установлена: {}", java_path)
                return java_path

        logger.warning("Не удалось найти java в {}", extract_dir)
        return None
    except Exception as exc:
        logger.error("Ошибка установки Java: {}", exc)
        return None
    finally:
        if archive_path.exists():
            try:
                archive_path.unlink()
            except Exception:
                pass


def ensure_java(min_version: int = 17) -> str | None:
    """Проверяет наличие подходящей Java и пытается установить при необходимости.

    Returns:
        Путь к java.exe/bin/java или None.
    """
    from quantumlauncher.core.java_detector import find_best_java

    existing = find_best_java(min_version)
    if existing:
        return str(existing.path)

    logger.info("Подходящая Java не найдена, начинаем автоматическую установку...")
    releases = fetch_java_releases(min_version)
    if not releases:
        return None

    best = releases[0]
    java_path = install_java(best.download_url)
    return str(java_path) if java_path else None
