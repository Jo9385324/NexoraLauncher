"""Главное окно QuantumLauncher."""

from pathlib import Path

import customtkinter as ctk
from loguru import logger

from quantumlauncher import __version__
from quantumlauncher.core.discord_rpc import DiscordRPC
from quantumlauncher.ui.pages.ai_chat_page import AIChatPage
from quantumlauncher.ui.pages.home_page import HomePage
from quantumlauncher.ui.pages.instances_page import InstancesPage
from quantumlauncher.ui.pages.maps_page import MapsPage
from quantumlauncher.ui.pages.modpacks_page import ModpacksPage
from quantumlauncher.ui.pages.mods_page import ModsPage
from quantumlauncher.ui.pages.resourcepacks_page import ResourcepacksPage
from quantumlauncher.ui.pages.servers_page import ServersPage
from quantumlauncher.ui.pages.settings_page import SettingsPage
from quantumlauncher.ui.pages.shaders_page import ShadersPage
from quantumlauncher.ui.pages.versions_page import VersionsPage
from quantumlauncher.utils.config import AppConfig
from quantumlauncher.utils.i18n import set_language, t


def _resolve_resources_path() -> Path:
    """Возвращает путь к директории ресурсов (pip или dev-режим)."""
    try:
        import importlib.resources as pkg_resources

        pkg_path = Path(str(pkg_resources.files("quantumlauncher")))
        return pkg_path.parent.parent / "resources"
    except Exception:
        # fallback для прямого запуска
        return Path(__file__).parent.parent.parent / "resources"


RESOURCES_PATH = _resolve_resources_path()


class MainWindow(ctk.CTk):
    """Главное окно приложения."""

    def __init__(self) -> None:
        super().__init__()

        self.config = AppConfig.load()
        set_language(self.config.language)
        self.title(t("app.title"))
        self.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.minsize(900, 600)

        # Устанавливаем иконку приложения
        self._set_app_icon()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_background()
        self._create_sidebar()
        self._create_content_area()
        self._create_status_bar()

        self.pages: dict[str, ctk.CTkFrame] = {}
        self._init_pages()
        self.show_page("home")

        self.discord_rpc = DiscordRPC()
        if self.discord_rpc.connect():
            self.discord_rpc.update_launcher()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        logger.debug("Главное окно инициализировано")

    def _set_app_icon(self) -> None:
        """Устанавливает иконку приложения."""
        try:
            icon_path = RESOURCES_PATH / "ico.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
                logger.debug("Иконка приложения установлена: {}", icon_path)
            else:
                logger.warning("Файл иконки не найден: {}", icon_path)
        except Exception as e:
            logger.warning("Не удалось установить иконку: {}", e)

    def _create_background(self) -> None:
        """Создаёт фоновое изображение."""
        try:
            bg_path = RESOURCES_PATH / "fron.png"
            if bg_path.exists():
                # Создаём фон с использованием PIL для загрузки изображения
                from PIL import Image

                bg_image = Image.open(str(bg_path))
                bg_image = bg_image.resize((1920, 1080), Image.Resampling.LANCZOS)

                self.bg_photo = ctk.CTkImage(light_image=bg_image, size=(1920, 1080))

                # Создаём лейбл для фона
                self.background_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
                self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
                self.background_label.lower()  # Помещаем фон на задний план
                logger.debug("Фон установлен: {}", bg_path)
            else:
                logger.warning("Файл фона не найден: {}", bg_path)
        except Exception as e:
            logger.warning("Не удалось установить фон: {}", e)

    def _create_sidebar(self) -> None:
        """Создаёт боковую панель навигации."""
        # Создаём контейнер с закруглёнными углами
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=15,
            fg_color=("#1e1e28", "#191923")
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Логотип с градиентным эффектом
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.logo_label = ctk.CTkLabel(
            logo_frame,
            text="Quantum\nLauncher",
            font=ctk.CTkFont(size=22, weight="bold"),
            justify="left"
        )
        self.logo_label.grid(row=0, column=0, sticky="w")

        # Разделитель
        separator = ctk.CTkFrame(self.sidebar, height=1, fg_color=("#3a3a45", "#404050"))
        separator.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("home", t("nav.home"), 1),
            ("instances", t("nav.instances"), 2),
            ("versions", t("nav.versions"), 3),
            ("mods", t("nav.mods"), 4),
            ("modpacks", t("nav.modpacks"), 5),
            ("maps", t("nav.maps"), 6),
            ("resourcepacks", t("nav.resourcepacks"), 7),
            ("shaders", t("nav.shaders"), 8),
            ("servers", t("nav.servers"), 9),
            ("ai", t("nav.ai"), 10),
            ("settings", t("nav.settings"), 11),
        ]

        for idx, (page_id, label, grid_row) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                corner_radius=8,
                height=36,
                font=ctk.CTkFont(size=13, weight="normal"),
                fg_color="transparent",
                text_color=("#a0a0a0", "#d0d0d0"),
                hover_color=("#3a3a45", "#404050"),
                command=lambda pid=page_id: self.show_page(pid),
            )
            btn.grid(row=grid_row, column=0, sticky="ew", padx=15, pady=2)
            self.nav_buttons[page_id] = btn

        # Версия внизу с улучшенным стилем
        version_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        version_frame.grid(row=12, column=0, padx=20, pady=(0, 5))

        self.version_label = ctk.CTkLabel(
            version_frame,
            text=f"v{__version__}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.version_label.grid(row=0, column=0)

        # Подпись разработчика
        author_label = ctk.CTkLabel(
            self.sidebar,
            text="Created by atomfren",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        author_label.grid(row=13, column=0, pady=(0, 15))

    def _create_content_area(self) -> None:
        """Создаёт область контента."""
        self.content_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=("#282832", "#1e1e28")
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    def _create_status_bar(self) -> None:
        """Создаёт статус-бар."""
        self.status_bar = ctk.CTkFrame(
            self,
            height=35,
            corner_radius=10,
            fg_color=("#23232d", "#1c1c26")
        )
        self.status_bar.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Готов",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(side="left", padx=15, pady=8)

    def _init_pages(self) -> None:
        """Инициализирует страницы."""
        self.pages["home"] = HomePage(self.content_frame, self)
        self.pages["instances"] = InstancesPage(self.content_frame, self)
        self.pages["versions"] = VersionsPage(self.content_frame, self)
        self.pages["mods"] = ModsPage(self.content_frame, self)
        self.pages["modpacks"] = ModpacksPage(self.content_frame, self)
        self.pages["maps"] = MapsPage(self.content_frame, self)
        self.pages["resourcepacks"] = ResourcepacksPage(self.content_frame, self)
        self.pages["shaders"] = ShadersPage(self.content_frame, self)
        self.pages["servers"] = ServersPage(self.content_frame, self)
        self.pages["ai"] = AIChatPage(self.content_frame, self)
        self.pages["settings"] = SettingsPage(self.content_frame, self)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def show_page(self, page_id: str) -> None:
        """Показывает указанную страницу."""
        if page_id not in self.pages:
            logger.warning("Страница {} не найдена", page_id)
            return

        for pid, page in self.pages.items():
            if pid == page_id:
                page.tkraise()
                # Активная кнопка с выделением
                self.nav_buttons[pid].configure(
                    fg_color=("#3a5a80", "#4a6a90"),
                    text_color=("#80b3ff", "#b3d9ff"),
                    font=ctk.CTkFont(size=14, weight="bold")
                )
            else:
                self.nav_buttons[pid].configure(
                    fg_color="transparent",
                    text_color=("#a0a0a0", "#d0d0d0"),
                    font=ctk.CTkFont(size=14, weight="normal")
                )

        self.set_status(f"Страница: {page_id}")
        logger.debug("Переключение на страницу {}", page_id)

    def set_status(self, text: str) -> None:
        """Устанавливает текст статус-бара."""
        self.status_label.configure(text=text)

    def on_closing(self) -> None:
        """Обработчик закрытия окна."""
        self.config.window_width = self.winfo_width()
        self.config.window_height = self.winfo_height()
        self.config.save()
        self.discord_rpc.close()
        self.destroy()
