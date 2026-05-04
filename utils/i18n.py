"""Интернационализация (i18n) для QuantumLauncher."""

import json
from pathlib import Path
from typing import Any

from loguru import logger

# Встроенные переводы (fallback)
_BUILTIN: dict[str, dict[str, str]] = {
    "ru": {
        "app.title": "QuantumLauncher",
        "nav.home": "🏠  Главная",
        "nav.instances": "📁  Инстансы",
        "nav.versions": "📦  Версии",
        "nav.mods": "🧩  Моды",
        "nav.modpacks": "📦  Модпаки",
        "nav.maps": "🗺️  Карты",
        "nav.resourcepacks": "🎨  Ресурспаки",
        "nav.shaders": "🌈  Шейдеры",
        "nav.servers": "🖥️  Серверы",
        "nav.ai": "🤖  AI Помощник",
        "nav.settings": "⚙️  Настройки",
        "servers.title": "Серверы",
        "servers.subtitle": "Управляйте своими серверами и подключайтесь к друзьям",
        "servers.add": "+ Добавить сервер",
        "servers.empty": "📭 Список серверов пуст",
        "servers.empty_hint": 'Нажмите "+ Добавить сервер", чтобы добавить свой первый сервер',
        "servers.refresh": "🔄 Обновить",
        "servers.join": "▶ Подключиться",
        "servers.delete": "🗑️",
        "servers.new_title": "Новый сервер",
        "servers.name_label": "Название сервера:",
        "servers.ip_label": "IP адрес:",
        "servers.port_label": "Порт (опционально):",
        "servers.port_hint": "По умолчанию: 25565",
        "servers.cancel": "Отмена",
        "servers.save": "💾 Добавить сервер",
        "servers.connect_msg": (
            "Подключение к серверу {name}\nIP: {host}:{port}\n\n"
            "Функция запуска с авто-подключением будет реализована позже."
        ),
        "servers.confirm_delete": 'Вы уверены, что хотите удалить сервер "{name}"?',
        "status.ready": "Готов",
        "launch.play": "▶  Запустить Minecraft",
        "launch.offline": "Офлайн",
        "launch.microsoft": "Microsoft",
        "launch.username": "Имя пользователя:",
        "launch.version": "Версия игры:",
        "launch.ms_login": "🔑 Войти через Microsoft",
        "launch.ms_client_id": "MS Client ID:",
        "error.select_version": "❌ Выберите версию",
        "error.enter_username": "❌ Введите имя пользователя",
        "error.ms_login_first": "❌ Сначала выполните вход в Microsoft",
        "status.launching": "🚀 Запуск Minecraft {}...",
        "status.running": "✅ Minecraft запущен (PID: {})",
        "status.closed": "👋 Minecraft закрыт",
        "crash.title": "Анализ краша",
        "crash.close": "Закрыть",
        "news.title": "📰  Последние обновления",
        "news.new": "НОВОЕ",
        "settings.title": "Настройки",
        "settings.language": "Язык",
        "settings.appearance": "Тема",
        "settings.memory": "Память (МБ)",
        "settings.java_path": "Путь к Java",
        "settings.jvm_profile": "Профиль JVM",
        "settings.save": "💾 Сохранить настройки",
        "settings.java_auto": "🔍 Авто",
        "settings.java_found": "✅ Найдено {count} Java",
        "settings.java_not_found": "❌ Java не найдена",
        "settings.saved": "✅ Настройки сохранены",
        "settings.save_error": "❌ Ошибка сохранения: {error}",
    },
    "en": {
        "app.title": "QuantumLauncher",
        "nav.home": "🏠  Home",
        "nav.instances": "📁  Instances",
        "nav.versions": "📦  Versions",
        "nav.mods": "🧩  Mods",
        "nav.modpacks": "📦  Modpacks",
        "nav.maps": "🗺️  Maps",
        "nav.resourcepacks": "🎨  Resource Packs",
        "nav.shaders": "🌈  Shaders",
        "nav.servers": "🖥️  Servers",
        "nav.ai": "🤖  AI Assistant",
        "nav.settings": "⚙️  Settings",
        "servers.title": "Servers",
        "servers.subtitle": "Manage your servers and connect to friends",
        "servers.add": "+ Add Server",
        "servers.empty": "📭 Server list is empty",
        "servers.empty_hint": 'Click "+ Add Server" to add your first server',
        "servers.refresh": "🔄 Refresh",
        "servers.join": "▶ Join",
        "servers.delete": "🗑️",
        "servers.new_title": "New Server",
        "servers.name_label": "Server name:",
        "servers.ip_label": "IP address:",
        "servers.port_label": "Port (optional):",
        "servers.port_hint": "Default: 25565",
        "servers.cancel": "Cancel",
        "servers.save": "💾 Add Server",
        "servers.connect_msg": (
            "Connecting to {name}\nIP: {host}:{port}\n\n"
            "Auto-connect launch will be implemented later."
        ),
        "servers.confirm_delete": 'Are you sure you want to delete server "{name}"?',
        "status.ready": "Ready",
        "launch.play": "▶  Launch Minecraft",
        "launch.offline": "Offline",
        "launch.microsoft": "Microsoft",
        "launch.username": "Username:",
        "launch.version": "Game version:",
        "launch.ms_login": "🔑 Login with Microsoft",
        "launch.ms_client_id": "MS Client ID:",
        "error.select_version": "❌ Select a version",
        "error.enter_username": "❌ Enter username",
        "error.ms_login_first": "❌ Log in with Microsoft first",
        "status.launching": "🚀 Launching Minecraft {}...",
        "status.running": "✅ Minecraft running (PID: {})",
        "status.closed": "👋 Minecraft closed",
        "crash.title": "Crash Analysis",
        "crash.close": "Close",
        "news.title": "📰  Latest Updates",
        "news.new": "NEW",
        "settings.title": "Settings",
        "settings.language": "Language",
        "settings.appearance": "Theme",
        "settings.memory": "Memory (MB)",
        "settings.java_path": "Java path",
        "settings.jvm_profile": "JVM profile",
        "settings.save": "💾 Save Settings",
        "settings.java_auto": "🔍 Auto",
        "settings.java_found": "✅ Found {count} Java",
        "settings.java_not_found": "❌ Java not found",
        "settings.saved": "✅ Settings saved",
        "settings.save_error": "❌ Save error: {error}",
    },
}

_current_lang = "ru"


def set_language(lang: str) -> None:
    """Устанавливает текущий язык."""
    global _current_lang
    if lang in _BUILTIN:
        _current_lang = lang
    else:
        logger.warning("Язык '{}' не поддерживается, используется 'ru'", lang)
        _current_lang = "ru"


def get_language() -> str:
    """Возвращает текущий язык."""
    return _current_lang


def t(key: str, **kwargs: Any) -> str:
    """Возвращает перевод по ключу с подстановкой переменных.

    Args:
        key: Ключ перевода, например "launch.play".
        **kwargs: Переменные для форматирования строки.

    Returns:
        Переведённая строка или сам ключ, если перевод не найден.
    """
    text = _BUILTIN.get(_current_lang, _BUILTIN["ru"]).get(key, key)
    try:
        return text.format(**kwargs)
    except KeyError:
        return text


def load_external_lang(path: Path) -> None:
    """Загружает внешний файл перевода и мержит с встроенным."""
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for lang, translations in data.items():
            if lang in _BUILTIN:
                _BUILTIN[lang].update(translations)
            else:
                _BUILTIN[lang] = dict(translations)
        logger.info("Загружен языковой файл: {}", path)
    except Exception as exc:
        logger.warning("Не удалось загрузить языковой файл {}: {}", path, exc)
