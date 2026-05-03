"""Система авторизации (офлайн + MS OAuth)."""

import json
import uuid
import webbrowser
from dataclasses import dataclass

import minecraft_launcher_lib as mll
from loguru import logger

from quantumlauncher.utils.paths import get_config_dir


@dataclass
class UserProfile:
    """Профиль пользователя."""

    username: str
    uuid: str
    access_token: str
    auth_type: str  # "offline" | "microsoft"
    refresh_token: str = ""


class AuthManager:
    """Менеджер авторизации."""

    REDIRECT_URI: str = "http://localhost:8080"

    @staticmethod
    def offline_login(username: str) -> UserProfile:
        """Офлайн авторизация (без проверки)."""
        user_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))
        return UserProfile(
            username=username,
            uuid=user_uuid,
            access_token="offline_token",
            auth_type="offline",
        )

    def microsoft_login_start(self, client_id: str) -> dict[str, str]:
        """Начинает MS OAuth flow.

        Returns:
            dict с ключами: url, state, code_verifier.
        """
        logger.info("Запуск MS OAuth авторизации")
        url, state, code_verifier = mll.microsoft_account.get_secure_login_data(
            client_id=client_id,
            redirect_uri=self.REDIRECT_URI,
        )
        logger.debug("MS OAuth URL: {}", url)
        return {
            "url": url,
            "state": state,
            "code_verifier": code_verifier,
        }

    def microsoft_login_complete(
        self,
        client_id: str,
        auth_code: str,
        code_verifier: str,
    ) -> UserProfile:
        """Завершает MS OAuth и возвращает профиль."""
        logger.info("Завершение MS OAuth авторизации")
        login_data = mll.microsoft_account.complete_login(
            client_id=client_id,
            client_secret=None,
            redirect_uri=self.REDIRECT_URI,
            auth_code=auth_code,
            code_verifier=code_verifier,
        )

        if "error" in login_data:
            raise RuntimeError(
                f"MS OAuth ошибка: {login_data.get('errorMessage', login_data['error'])}"
            )

        profile = UserProfile(
            username=login_data["name"],
            uuid=login_data["id"],
            access_token=login_data["access_token"],
            auth_type="microsoft",
            refresh_token=login_data.get("refresh_token", ""),
        )
        self._save_profile(profile)
        logger.info("MS OAuth успешен: {}", profile.username)
        return profile

    def microsoft_refresh(self, client_id: str, refresh_token: str) -> UserProfile:
        """Обновляет access_token через refresh_token."""
        logger.info("Обновление MS токена")
        login_data = mll.microsoft_account.complete_refresh(
            client_id=client_id,
            client_secret=None,
            redirect_uri=self.REDIRECT_URI,
            refresh_token=refresh_token,
        )

        if "error" in login_data:
            raise RuntimeError(
                f"MS Refresh ошибка: {login_data.get('errorMessage', login_data['error'])}"
            )

        profile = UserProfile(
            username=login_data["name"],
            uuid=login_data["id"],
            access_token=login_data["access_token"],
            auth_type="microsoft",
            refresh_token=login_data.get("refresh_token", refresh_token),
        )
        self._save_profile(profile)
        logger.info("MS токен обновлён: {}", profile.username)
        return profile

    def _save_profile(self, profile: UserProfile) -> None:
        """Сохраняет профиль в файл."""
        path = get_config_dir() / "ms_profile.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "username": profile.username,
                    "uuid": profile.uuid,
                    "auth_type": profile.auth_type,
                    "refresh_token": profile.refresh_token,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load_saved_profile(cls) -> UserProfile | None:
        """Загружает сохранённый MS профиль."""
        path = get_config_dir() / "ms_profile.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return UserProfile(
                username=data["username"],
                uuid=data["uuid"],
                access_token="",
                auth_type=data.get("auth_type", "microsoft"),
                refresh_token=data.get("refresh_token", ""),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def open_browser(self, url: str) -> None:
        """Открывает URL в браузере."""
        logger.debug("Открытие браузера: {}", url)
        webbrowser.open(url)

    @staticmethod
    def _extract_auth_code(url_or_code: str) -> str:
        """Извлекает auth code из URL или возвращает как есть."""
        if url_or_code.startswith("http"):
            # Это URL вида http://localhost:8080?code=ABC&state=XYZ
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(url_or_code)
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            if not code:
                raise ValueError("Не найден параметр 'code' в URL")
            return code
        # Предполагаем, что это уже код
        return url_or_code
