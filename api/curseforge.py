"""Клиент API CurseForge для поиска модов.

Требует API ключ (можно получить бесплатно на https://console.curseforge.com/).
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp
from loguru import logger

from quantumlauncher.utils.paths import get_cache_dir

CURSEFORGE_API_URL = "https://api.curseforge.com/v1"
_CACHE_TTL = 300


@dataclass
class CurseForgeMod:
    """Мод на CurseForge."""

    mod_id: int
    name: str
    summary: str
    slug: str
    download_count: int
    thumbnail_url: str
    game_version: list[str]
    categories: list[str]


class _Cache:
    def __init__(self) -> None:
        self._dir = get_cache_dir() / "curseforge"
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
            if now - ts < _CACHE_TTL:
                return value
            del self._mem[key]
        path = self._path(key)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if now - data.get("_ts", 0) < _CACHE_TTL:
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
            logger.debug("Ошибка записи кэша CurseForge: {}", exc)


class CurseForgeClient:
    """Асинхронный клиент CurseForge API."""

    def __init__(self, api_key: str, base_url: str = CURSEFORGE_API_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self._session: aiohttp.ClientSession | None = None
        self._cache = _Cache()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Accept": "application/json",
                    "x-api-key": self.api_key,
                    "User-Agent": "QuantumLauncher/0.1.0",
                }
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def search(
        self,
        query: str,
        game_version: str | None = None,
        mod_loader_type: int | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[CurseForgeMod]:
        """Ищет моды по запросу.

        Args:
            mod_loader_type: 1=Forge, 4=Fabric, 5=Quilt.
        """
        cache_key = self._cache._key(
            "search", query, str(game_version), str(mod_loader_type), str(limit), str(offset)
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("CurseForge search '{}' из кэша", query)
            return [CurseForgeMod(**m) for m in cached]

        session = await self._get_session()
        params: dict[str, Any] = {
            "gameId": 432,  # Minecraft
            "searchFilter": query,
            "pageSize": limit,
            "index": offset,
            "sortField": 2,  # по популярности
            "sortOrder": "desc",
        }
        if game_version:
            params["gameVersion"] = game_version
        if mod_loader_type is not None:
            params["modLoaderType"] = mod_loader_type

        async with session.get(f"{self.base_url}/mods/search", params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

        hits = data.get("data", [])
        logger.debug("CurseForge search '{}' returned {} results", query, len(hits))

        result: list[CurseForgeMod] = []
        for h in hits:
            thumbs = h.get("logo", {})
            thumb_url = thumbs.get("thumbnailUrl", "") if isinstance(thumbs, dict) else ""
            result.append(
                CurseForgeMod(
                    mod_id=h["id"],
                    name=h["name"],
                    summary=h.get("summary", ""),
                    slug=h.get("slug", ""),
                    download_count=h.get("downloadCount", 0),
                    thumbnail_url=thumb_url,
                    game_version=h.get("latestFilesIndexes", [{}])[0].get("gameVersion", ""),
                    categories=[c["name"] for c in h.get("categories", [])],
                )
            )
        self._cache.set(cache_key, [r.__dict__ for r in result])
        return result

    async def get_mod_files(
        self,
        mod_id: int,
        game_version: str | None = None,
        mod_loader_type: int | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Возвращает список файлов мода."""
        cache_key = self._cache._key(
            "files", str(mod_id), str(game_version), str(mod_loader_type), str(limit)
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        session = await self._get_session()
        params: dict[str, Any] = {"pageSize": limit}
        if game_version:
            params["gameVersion"] = game_version
        if mod_loader_type is not None:
            params["modLoaderType"] = mod_loader_type

        async with session.get(
            f"{self.base_url}/mods/{mod_id}/files", params=params
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        files = data.get("data", [])
        self._cache.set(cache_key, files)
        return files

    async def download_mod_file(self, url: str, dest: str) -> None:
        """Скачивает файл по прямой ссылке."""
        session = await self._get_session()
        async with session.get(url) as resp:
            resp.raise_for_status()
            with open(dest, "wb") as f:
                async for chunk in resp.content.iter_chunked(8192):
                    f.write(chunk)
        logger.info("Файл скачан: {}", dest)

    async def __aenter__(self) -> "CurseForgeClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
