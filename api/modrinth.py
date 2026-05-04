"""Клиент API Modrinth для поиска и скачивания модов."""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import aiohttp
from loguru import logger

from quantumlauncher.utils.paths import get_cache_dir

MODRINTH_API_URL = "https://api.modrinth.com/v2"
_CACHE_TTL_SECONDS = 300  # 5 минут


@dataclass
class ModrinthProject:
    """Проект (мод) на Modrinth."""

    project_id: str
    slug: str
    title: str
    description: str
    categories: list[str]
    downloads: int
    icon_url: str | None
    game_versions: list[str]
    loaders: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModrinthProject":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ModrinthVersion:
    """Версия мода на Modrinth."""

    version_id: str
    project_id: str
    version_number: str
    game_versions: list[str]
    loaders: list[str]
    files: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModrinthVersion":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class _Cache:
    """Простой файловый + in-memory кэш для Modrinth."""

    def __init__(self) -> None:
        self._dir = get_cache_dir() / "modrinth"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._mem: dict[str, tuple[Any, float]] = {}

    def _key(self, *parts: str) -> str:
        return "_".join(parts).replace(" ", "_")[:120]

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, key: str) -> Any | None:
        now = time.time()
        if key in self._mem:
            value, ts = self._mem[key]
            if now - ts < _CACHE_TTL_SECONDS:
                return value
            del self._mem[key]

        path = self._path(key)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if now - data.get("_ts", 0) < _CACHE_TTL_SECONDS:
                    self._mem[key] = (data["value"], data["_ts"])
                    return data["value"]
            except Exception:
                pass
        return None

    def set(self, key: str, value: Any) -> None:
        now = time.time()
        self._mem[key] = (value, now)
        try:
            self._path(key).write_text(
                json.dumps({"_ts": now, "value": value}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug("Ошибка записи кэша Modrinth: {}", exc)


class ModrinthClient:
    """Асинхронный клиент Modrinth API."""

    def __init__(self, base_url: str = MODRINTH_API_URL) -> None:
        self.base_url = base_url
        self._session: aiohttp.ClientSession | None = None
        self._cache = _Cache()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Возвращает или создаёт сессию."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "QuantumLauncher/0.1.0 (quantumlauncher@example.com)",
                }
            )
        return self._session

    async def close(self) -> None:
        """Закрывает сессию."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def search(
        self,
        query: str,
        facets: list[list[str]] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ModrinthProject]:
        """Ищет моды по запросу (с кэшированием)."""
        cache_key = self._cache._key("search", query, str(facets), str(limit), str(offset))
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("Modrinth search '{}' из кэша", query)
            return [ModrinthProject.from_dict(h) for h in cached]

        session = await self._get_session()
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }
        if facets:
            params["facets"] = json.dumps(facets)

        async with session.get(f"{self.base_url}/search", params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

        hits = data.get("hits", [])
        logger.debug("Modrinth search '{}' returned {} results", query, len(hits))

        result = [
            ModrinthProject(
                project_id=h["project_id"],
                slug=h["slug"],
                title=h["title"],
                description=h["description"],
                categories=h.get("categories", []),
                downloads=h.get("downloads", 0),
                icon_url=h.get("icon_url"),
                game_versions=h.get("versions", []),
                loaders=h.get("display_categories", []),
            )
            for h in hits
        ]
        self._cache.set(cache_key, [r.to_dict() for r in result])
        return result

    async def get_featured_projects(
        self,
        project_type: str | None = None,
        limit: int = 12,
    ) -> list[ModrinthProject]:
        """Возвращает популярные/рекомендуемые проекты."""
        facets: list[list[str]] = []
        if project_type:
            facets.append([f"project_type:{project_type}"])

        params: dict[str, Any] = {
            "limit": limit,
            "index": "featured",
        }
        if facets:
            params["facets"] = json.dumps(facets)

        session = await self._get_session()
        async with session.get(f"{self.base_url}/search", params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

        hits = data.get("hits", [])
        return [
            ModrinthProject(
                project_id=h["project_id"],
                slug=h["slug"],
                title=h["title"],
                description=h.get("description", ""),
                categories=h.get("categories", []),
                downloads=h.get("downloads", 0),
                icon_url=h.get("icon_url"),
                game_versions=h.get("versions", []),
                loaders=h.get("display_categories", []),
            )
            for h in hits
        ]

    async def get_project_versions(
        self,
        project_id: str,
        game_version: str | None = None,
        loader: str | None = None,
    ) -> list[ModrinthVersion]:
        """Возвращает версии проекта (с кэшированием)."""
        cache_key = self._cache._key("versions", project_id, str(game_version), str(loader))
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("Modrinth versions '{}' из кэша", project_id)
            return [ModrinthVersion.from_dict(v) for v in cached]

        session = await self._get_session()
        params: dict[str, Any] = {}
        if game_version:
            params["game_versions"] = f'["{game_version}"]'
        if loader:
            params["loaders"] = f'["{loader}"]'

        async with session.get(
            f"{self.base_url}/project/{project_id}/version", params=params
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        result = [
            ModrinthVersion(
                version_id=v["id"],
                project_id=v["project_id"],
                version_number=v["version_number"],
                game_versions=v.get("game_versions", []),
                loaders=v.get("loaders", []),
                files=v.get("files", []),
            )
            for v in data
        ]
        self._cache.set(cache_key, [r.to_dict() for r in result])
        return result

    async def get_best_version(
        self,
        project_id: str,
        game_version: str,
        loader: str,
    ) -> ModrinthVersion | None:
        """Возвращает лучшую подходящую версию мода."""
        versions = await self.get_project_versions(project_id, game_version, loader)
        if not versions:
            return None
        # Берём первую (самую новую) подходящую
        return versions[0]

    def get_primary_file(self, version: ModrinthVersion) -> dict[str, Any] | None:
        """Возвращает primary файл из версии."""
        for file_info in version.files:
            if file_info.get("primary", False):
                return file_info
        # Если primary не указан — берём первый
        return version.files[0] if version.files else None

    async def download_mod(
        self,
        version: ModrinthVersion,
        dest_dir: str,
    ) -> str:
        """Скачивает мод в указанную директорию.

        Returns:
            Путь к скачанному файлу.
        """
        file_info = self.get_primary_file(version)
        if file_info is None:
            raise ValueError("Нет файлов для скачивания")

        url = file_info["url"]
        filename = file_info["filename"]
        dest_path = Path(dest_dir) / filename
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        await self.download_file(url, str(dest_path))
        return str(dest_path)

    async def download_file(self, url: str, dest: str) -> None:
        """Скачивает файл по URL."""
        session = await self._get_session()
        async with session.get(url) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                async for chunk in resp.content.iter_chunked(8192):
                    f.write(chunk)
        logger.info("Файл скачан: {}", dest)

    async def __aenter__(self) -> "ModrinthClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
