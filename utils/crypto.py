"""Шифрование чувствительных данных (токены, пароли).

Если cryptography не установлена, токены хранятся в открытом виде
с предупреждением в логе. Для production установите cryptography:
    pip install cryptography
"""

import base64
import hashlib
import os
from pathlib import Path
from typing import Any

from loguru import logger

try:
    from cryptography.fernet import Fernet

    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False
    logger.warning(
        "cryptography не установлена. Токены будут храниться без шифрования. "
        "Установите: pip install cryptography"
    )


def _derive_key(machine_specific: bytes) -> bytes:
    """Генерирует стабильный ключ из machine-specific данных."""
    digest = hashlib.sha256(machine_specific).digest()
    return base64.urlsafe_b64encode(digest)


def _get_machine_key() -> bytes:
    """Возвращает machine-specific строку для привязки шифрования к ПК."""
    parts: list[str] = []

    # Windows: имя компьютера + имя пользователя
    if os.name == "nt":
        parts.extend([os.environ.get("COMPUTERNAME", ""), os.environ.get("USERNAME", "")])
    else:
        parts.extend([os.environ.get("HOSTNAME", ""), os.environ.get("USER", "")])

    # Добавляем путь к домашней директории (стабилен для пользователя)
    parts.append(str(Path.home()))

    return "|".join(parts).encode("utf-8", errors="ignore")


class TokenVault:
    """Хранилище зашифрованных токенов с привязкой к машине.

    Fallback: если cryptography недоступна, возвращает plaintext.
    """

    _fernet: Any | None = None
    _warned = False

    @classmethod
    def _get_fernet(cls) -> Any:
        if not _HAS_CRYPTO:
            return None
        if cls._fernet is None:
            key = _derive_key(_get_machine_key())
            cls._fernet = Fernet(key)
        return cls._fernet

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Шифрует строку, возвращает base64."""
        if not plaintext:
            return ""
        if not _HAS_CRYPTO:
            if not cls._warned:
                cls._warned = True
                logger.warning("Шифрование отключено: cryptography не установлена")
            return plaintext
        try:
            f = cls._get_fernet()
            token = f.encrypt(plaintext.encode("utf-8"))
            return token.decode("utf-8")
        except Exception as exc:
            logger.warning("Ошибка шифрования: {}", exc)
            return ""

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """Дешифрует строку. При ошибке возвращает пустую строку."""
        if not ciphertext:
            return ""
        if not _HAS_CRYPTO:
            return ciphertext
        try:
            f = cls._get_fernet()
            return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            logger.warning("Ошибка дешифрования (возможно, смена ПК/ключа): {}", exc)
            return ""
