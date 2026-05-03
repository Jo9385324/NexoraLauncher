"""
Стили и компоненты для UI QuantumLauncher.
Премиальный футуристичный дизайн с неоновыми акцентами и glassmorphism.
"""

import customtkinter as ctk


# Цветовые палитры - Premium Cyberpunk Theme
class Colors:
    """Цветовые палитры для премиум темы."""

    # Глубокий фон (void black)
    VOID_BLACK = "#0a0a0f"
    VOID_DARKER = "#050508"

    # Неоновые акценты - Electric Cyan & Vibrant Purple
    NEON_CYAN = "#00f5ff"
    NEON_CYON_DARK = "#00c8d4"
    NEON_PURPLE = "#bf00ff"
    NEON_PURPLE_DARK = "#9900cc"

    # Градиентные акценты
    PRIMARY_GRADIENT_START = "#00f5ff"
    PRIMARY_GRADIENT_END = "#bf00ff"

    # Вторичные цвета
    SECONDARY = "#1a1a24"
    SECONDARY_DARK = "#12121a"

    # Glassmorphic панели
    GLASS_LIGHT = "rgba(30, 30, 45, 0.7)"
    GLASS_DARK = "rgba(20, 20, 30, 0.8)"
    GLASS_BORDER = "rgba(0, 245, 255, 0.3)"

    # Карточки с неоновым свечением
    CARD_LIGHT = "#14141f"
    CARD_DARK = "#0d0d14"

    # Границы с свечением
    BORDER_GLOW_LIGHT = "rgba(0, 245, 255, 0.4)"
    BORDER_GLOW_DARK = "rgba(191, 0, 255, 0.4)"

    # Текст - высокий контраст
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b8b8d0"
    TEXT_MUTED = "#707080"
    TEXT_NEON_CYAN = "#00f5ff"
    TEXT_NEON_PURPLE = "#bf00ff"

    # Внутренние подсветки
    INNER_HIGHLIGHT = "rgba(255, 255, 255, 0.08)"

    # Успех/ошибка/предупреждение
    SUCCESS = "#00ff88"
    ERROR = "#ff0055"
    WARNING = "#ffaa00"

    # Nebula effect colors
    NEBULA_PURPLE = "rgba(191, 0, 255, 0.1)"
    NEBULA_CYAN = "rgba(0, 245, 255, 0.08)"


def create_card_frame(
    parent,
    fg_color: str | None = None,
    corner_radius: int = 12,
    border_width: int = 1,
    **kwargs
) -> ctk.CTkFrame:
    """Создаёт карточку с современным дизайном.

    Args:
        parent: Родительский виджет
        fg_color: Цвет фона
        corner_radius: Радиус закругления углов
        border_width: Ширина границы

    Returns:
        CTkFrame с настроенными стилями
    """
    if fg_color is None:
        fg_color = Colors.CARD_LIGHT

    return ctk.CTkFrame(
        parent,
        fg_color=fg_color,
        corner_radius=corner_radius,
        border_width=border_width,
        border_color=Colors.BORDER_LIGHT,
        **kwargs
    )


def create_nav_button(
    parent,
    text: str,
    command,
    is_active: bool = False
) -> ctk.CTkButton:
    """Создаёт навигационную кнопку.

    Args:
        parent: Родительский виджет
        text: Текст кнопки
        command: Функция вызова
        is_active: Активна ли кнопка

    Returns:
        CTkButton с настроенными стилями
    """
    if is_active:
        fg_color = Colors.PRIMARY
        text_color = Colors.PRIMARY_TEXT_LIGHT
        font_weight = "bold"
    else:
        fg_color = "transparent"
        text_color = Colors.TEXT_SECONDARY
        font_weight = "normal"

    return ctk.CTkButton(
        parent,
        text=text,
        anchor="w",
        corner_radius=8,
        height=38,
        font=ctk.CTkFont(size=14, weight=font_weight),
        fg_color=fg_color,
        text_color=text_color,
        hover_color=Colors.SECONDARY,
        command=command
    )


def create_primary_button(
    parent,
    text: str,
    command,
    width: int = 140,
    height: int = 40,
    font_size: int = 14
) -> ctk.CTkButton:
    """Создаёт основную кнопку действия.

    Args:
        parent: Родительский виджет
        text: Текст кнопки
        command: Функция вызова
        width: Ширина кнопки
        height: Высота кнопки
        font_size: Размер шрифта

    Returns:
        CTkButton с настроенными стилями
    """
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        font=ctk.CTkFont(size=font_size, weight="bold"),
        corner_radius=10
    )


def create_secondary_button(
    parent,
    text: str,
    command,
    width: int = 120,
    height: int = 40,
    font_size: int = 13
) -> ctk.CTkButton:
    """Создаёт вторичную кнопку (отмена, назад).

    Args:
        parent: Родительский виджет
        text: Текст кнопки
        command: Функция вызова
        width: Ширина кнопки
        height: Высота кнопки
        font_size: Размер шрифта

    Returns:
        CTkButton с настроенными стилями
    """
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        font=ctk.CTkFont(size=font_size, weight="bold"),
        corner_radius=8,
        fg_color="transparent",
        text_color=Colors.TEXT_SECONDARY,
        hover_color=Colors.SECONDARY
    )


def create_entry(
    parent,
    placeholder_text: str = "",
    width: int | None = None,
    height: int = 38
) -> ctk.CTkEntry:
    """Создаёт поле ввода.

    Args:
        parent: Родительский виджет
        placeholder_text: Текст-заполнитель
        width: Ширина поля
        height: Высота поля

    Returns:
        CTkEntry с настроенными стилями
    """
    kwargs = {"placeholder_text": placeholder_text, "height": height}
    if width:
        kwargs["width"] = width

    return ctk.CTkEntry(
        parent,
        font=ctk.CTkFont(size=13),
        corner_radius=10,
        **kwargs
    )


def create_label(
    parent,
    text: str = "",
    font_size: int = 14,
    weight: str = "normal",
    text_color: tuple[str, str] | str | None = None
) -> ctk.CTkLabel:
    """Создаёт текстовую метку.

    Args:
        parent: Родительский виджет
        text: Текст метки
        font_size: Размер шрифта
        weight: Начертание (normal/bold)
        text_color: Цвет текста

    Returns:
        CTkLabel с настроенными стилями
    """
    kwargs = {"text": text, "font": ctk.CTkFont(size=font_size, weight=weight)}
    if text_color:
        kwargs["text_color"] = text_color

    return ctk.CTkLabel(parent, **kwargs)
