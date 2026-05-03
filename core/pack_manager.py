"""Импорт/экспорт инстансов (.zip / .mrpack)."""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import requests
from loguru import logger

from quantumlauncher.core.instance import Instance
from quantumlauncher.utils.paths import get_instances_dir


def _sha1_hash(path: Path) -> str:
    """Вычисляет SHA1 хэш файла."""
    h = hashlib.sha1()
    with path.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def export_instance(instance: Instance, output_path: Path) -> None:
    """Экспортирует инстанс в .zip архив."""
    output_path = output_path.with_suffix(".zip")
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in instance.path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(instance.path)
                zf.write(file_path, arcname)
    logger.info("Инстанс '{}' экспортирован в {}", instance.name, output_path)


def import_zip(zip_path: Path, new_name: str) -> Instance:
    """Импортирует .zip архив как новый инстанс."""
    target = get_instances_dir() / new_name
    if target.exists():
        raise FileExistsError(f"Инстанс '{new_name}' уже существует")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target)

    # Пытаемся загрузить метаданные
    instance = Instance.load(new_name)
    if instance:
        instance.name = new_name
        instance.save()
        logger.info("Инстанс '{}' импортирован из {}", new_name, zip_path)
        return instance

    # Если instance.json нет — создаём базовый
    instance = Instance(name=new_name, version="unknown")
    instance.save()
    logger.info("Инстанс '{}' создан из архива без метаданных", new_name)
    return instance


def _download_file(url: str, dest: Path, expected_hash: str = "") -> None:
    """Скачивает файл по URL с проверкой хэша."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.debug("Скачивание {} -> {}", url, dest)
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    if expected_hash and _sha1_hash(dest) != expected_hash:
        dest.unlink()
        raise ValueError(f"SHA1 mismatch для {dest.name}")


def import_mrpack(mrpack_path: Path, new_name: str) -> Instance:
    """Импортирует .mrpack (Modrinth pack) как новый инстанс."""
    target = get_instances_dir() / new_name
    if target.exists():
        raise FileExistsError(f"Инстанс '{new_name}' уже существует")

    target.mkdir(parents=True)

    # Распаковываем mrpack
    with zipfile.ZipFile(mrpack_path, "r") as zf:
        zf.extractall(target)

    index_path = target / "modrinth.index.json"
    version = "unknown"
    mod_loader = "vanilla"
    loader_version = ""

    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            # Скачиваем файлы
            for entry in index.get("files", []):
                file_path = target / entry["path"]
                downloads = entry.get("downloads", [])
                if not downloads:
                    logger.warning("Нет ссылок для {}", entry["path"])
                    continue
                hashes = entry.get("hashes", {})
                expected = hashes.get("sha1", "")
                try:
                    _download_file(downloads[0], file_path, expected)
                except Exception as exc:
                    logger.error("Ошибка скачивания {}: {}", entry["path"], exc)
                    raise

            # Метаданные
            deps = index.get("dependencies", {})
            if "minecraft" in deps:
                version = deps["minecraft"]
            if "forge" in deps:
                mod_loader = "forge"
                loader_version = deps["forge"]
            elif "fabric-loader" in deps:
                mod_loader = "fabric"
                loader_version = deps["fabric-loader"]
            elif "quilt-loader" in deps:
                mod_loader = "quilt"
                loader_version = deps["quilt-loader"]
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Ошибка парсинга modrinth.index.json: {}", exc)

    # Перемещаем overrides в .minecraft
    overrides = target / "overrides"
    if overrides.exists():
        game_dir = target / ".minecraft"
        game_dir.mkdir(exist_ok=True)
        for item in overrides.iterdir():
            dest = game_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))
        overrides.rmdir()

    instance = Instance(
        name=new_name,
        version=version,
        mod_loader=mod_loader,
        loader_version=loader_version,
    )
    instance.save()
    logger.info("Инстанс '{}' импортирован из mrpack {}", new_name, mrpack_path)
    return instance
