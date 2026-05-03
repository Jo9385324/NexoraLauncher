"""Работа со скинами Minecraft."""

from pathlib import Path

import requests
from loguru import logger
from PIL import Image

from quantumlauncher.utils.paths import get_cache_dir

MOJANG_PROFILE_URL = "https://api.mojang.com/users/profiles/minecraft/{username}"
MOJANG_SESSION_URL = "https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"


class SkinManager:
    """Менеджер скинов Minecraft."""

    def __init__(self) -> None:
        self.cache_dir = get_cache_dir() / "skins"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_uuid(self, username: str) -> str | None:
        """Получает UUID по имени пользователя."""
        try:
            resp = requests.get(
                MOJANG_PROFILE_URL.format(username=username),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("id")
        except Exception as exc:
            logger.warning("Не удалось получить UUID для {}: {}", username, exc)
            return None

    def get_skin_url(self, uuid: str) -> str | None:
        """Получает URL скина по UUID."""
        try:
            resp = requests.get(
                MOJANG_SESSION_URL.format(uuid=uuid),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            for prop in data.get("properties", []):
                if prop["name"] == "textures":
                    import base64
                    import json

                    textures = json.loads(
                        base64.b64decode(prop["value"]).decode("utf-8")
                    )
                    return textures.get("textures", {}).get("SKIN", {}).get("url")
            return None
        except Exception as exc:
            logger.warning("Не удалось получить скин для {}: {}", uuid, exc)
            return None

    def download_skin(self, url: str, username: str) -> Path:
        """Скачивает скин в кэш.

        Returns:
            Путь к файлу скина.
        """
        cache_path = self.cache_dir / f"{username}.png"
        if cache_path.exists():
            return cache_path

        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        cache_path.write_bytes(resp.content)
        logger.info("Скин {} скачан", username)
        return cache_path

    def get_skin_image(self, username: str) -> Image.Image | None:
        """Возвращает PIL Image скина по имени пользователя."""
        cache_path = self.cache_dir / f"{username}.png"
        if cache_path.exists():
            return Image.open(cache_path)

        uuid = self.get_uuid(username)
        if not uuid:
            return None

        url = self.get_skin_url(uuid)
        if not url:
            return None

        path = self.download_skin(url, username)
        return Image.open(path)

    def render_preview(self, skin_img: Image.Image, scale: int = 4) -> Image.Image:
        """Рендерит 2D превью скина (вид спереди).

        Args:
            skin_img: Исходное изображение скина.
            scale: Масштаб пикселей.

        Returns:
            PIL Image превью.
        """
        # Размеры скина
        sw, sh = skin_img.size
        is_new_format = sh >= 64

        # Размеры превью
        pw, ph = 16 * scale, 32 * scale
        preview = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))

        def draw_region(
            src_x: int, src_y: int, src_w: int, src_h: int,
            dst_x: int, dst_y: int,
        ) -> None:
            """Копирует область скина в превью."""
            region = skin_img.crop((src_x, src_y, src_x + src_w, src_y + src_h))
            region = region.resize((src_w * scale, src_h * scale), Image.NEAREST)
            preview.paste(region, (dst_x * scale, dst_y * scale))

        # Голова (8x8) -> позиция (4, 0)
        draw_region(8, 8, 8, 8, 4, 0)

        # Тело (8x12) -> позиция (4, 8)
        if is_new_format:
            draw_region(20, 20, 8, 12, 4, 8)
        else:
            draw_region(20, 20, 8, 12, 4, 8)

        # Руки (4x12)
        draw_region(44, 20, 4, 12, 0, 8)
        draw_region(36 if is_new_format else 44, 52 if is_new_format else 20, 4, 12, 12, 8)

        # Ноги (4x12)
        draw_region(4, 20, 4, 12, 4, 20)
        draw_region(20 if is_new_format else 4, 52 if is_new_format else 20, 4, 12, 8, 20)

        return preview

    def render_head(self, skin_img: Image.Image, scale: int = 8) -> Image.Image:
        """Рендерит только голову скина."""
        preview = Image.new("RGBA", (8 * scale, 8 * scale), (0, 0, 0, 0))

        region = skin_img.crop((8, 8, 16, 16))
        region = region.resize((8 * scale, 8 * scale), Image.NEAREST)
        preview.paste(region, (0, 0))

        # Слой шлема (overlay)
        sw, sh = skin_img.size
        if sh >= 64:
            overlay = skin_img.crop((40, 8, 48, 16))
            overlay = overlay.resize((8 * scale, 8 * scale), Image.NEAREST)
            preview = Image.alpha_composite(preview, overlay)

        return preview
