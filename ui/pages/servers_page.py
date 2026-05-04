"""
Страница управления серверами в лаунчере.
Показывает список серверов с пингом, MOTD, возможность быстрого подключения.
"""

import asyncio
import threading
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw

from quantumlauncher.core.server_manager import ServerInfo, ServerManager
from quantumlauncher.core.server_ping import ServerStatus
from quantumlauncher.utils.i18n import t


def create_server_placeholder(color: str = "#3a7ebf") -> Image.Image:
    """Создаёт заглушку для иконки сервера."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Круг с градиентом (упрощённый)
    draw.ellipse([4, 4, 60, 60], fill=color)
    draw.ellipse([12, 12, 52, 52], fill="#ffffff20")

    # Иконка сервера
    draw.rectangle([24, 20, 40, 24], fill="white")
    draw.rectangle([20, 28, 44, 36], fill="white")
    draw.rectangle([24, 40, 40, 44], fill="white")

    return img


class ServersPage(ctk.CTkFrame):
    """Страница списка серверов."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.server_manager = ServerManager()
        self._server_images: dict[str, Image.Image] = {}
        # Храним ссылки на виджеты для обновления пинга/MOTD
        self._server_widgets: dict[str, dict] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._setup_ui()
        self._load_servers()

    def _setup_ui(self) -> None:
        """Настройка интерфейса страницы."""
        # Заголовок с улучшенным дизайном
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        title = ctk.CTkLabel(
            title_frame,
            text=t("servers.title"),
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(side="left")

        subtitle = ctk.CTkLabel(
            title_frame,
            text=t("servers.subtitle"),
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        subtitle.pack(side="left", padx=(15, 0), pady=(8, 0))

        # Кнопка добавления с иконкой
        add_btn = ctk.CTkButton(
            header_frame,
            text=t("servers.add"),
            command=self._add_server_dialog,
            width=160,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10
        )
        add_btn.pack(side="right")

        # Панель статистики
        stats_frame = ctk.CTkFrame(
            self,
            fg_color=("#323241", "#2d2d3c"),
            corner_radius=10
        )
        stats_frame.pack(fill="x", padx=30, pady=(0, 20))

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=20, pady=12)

        self.servers_count_label = ctk.CTkLabel(
            stats_inner,
            text="0 серверов",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("light blue", "light blue")
        )
        self.servers_count_label.pack(side="left")

        refresh_btn = ctk.CTkButton(
            stats_inner,
            text=t("servers.refresh"),
            command=self._refresh_all_servers,
            width=100,
            height=30,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            fg_color="transparent",
            text_color=("gray70", "gray85"),
            hover_color=("#3a3a45", "#404050")
        )
        refresh_btn.pack(side="right")

        # Список серверов
        self.servers_list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.servers_list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

    def _load_servers(self) -> None:
        """Загрузка и отображение серверов."""
        # Очищаем список
        for widget in self.servers_list_frame.winfo_children():
            widget.destroy()

        self._server_images.clear()
        self._server_widgets.clear()

        servers = self.server_manager.get_all_servers()

        # Обновляем статистику
        self.servers_count_label.configure(text=f"{len(servers)} серверов")

        if not servers:
            empty_frame = ctk.CTkFrame(self.servers_list_frame, fg_color="transparent")
            empty_frame.pack(expand=True, pady=60)

            empty_label = ctk.CTkLabel(
                empty_frame,
                text=t("servers.empty"),
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="gray"
            )
            empty_label.pack(pady=(0, 10))

            empty_subtitle = ctk.CTkLabel(
                empty_frame,
                text=t("servers.empty_hint"),
                font=ctk.CTkFont(size=13),
                text_color="gray"
            )
            empty_subtitle.pack()
            return

        # Отображаем каждый сервер
        for server in servers:
            self._create_server_card(server)

        # Обновляем информацию о серверах (асинхронно в отдельном потоке)
        self._refresh_all_servers()

    def _create_server_card(self, server: ServerInfo) -> None:
        """Создание карточки сервера."""
        card = ctk.CTkFrame(
            self.servers_list_frame,
            fg_color=("#323241", "#2d2d3c"),
            corner_radius=12,
            border_width=1,
            border_color=("#505064", "#46465a")
        )
        card.pack(fill="x", pady=8, padx=5)

        # Левая часть: иконка, имя и IP
        left_frame = ctk.CTkFrame(card, fg_color="transparent")
        left_frame.pack(fill="x", padx=15, pady=12, side="left", expand=True)

        # Верхняя строка: иконка и имя
        top_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 6))

        # Иконка сервера
        if server.name not in self._server_images:
            self._server_images[server.name] = create_server_placeholder()

        img = self._server_images[server.name]
        img_ctk = ctk.CTkImage(img, size=(48, 48))
        icon_label = ctk.CTkLabel(top_row, image=img_ctk, text="")
        icon_label.pack(side="left", padx=(2, 12))

        name_label = ctk.CTkLabel(
            top_row,
            text=server.name,
            font=ctk.CTkFont(size=17, weight="bold")
        )
        name_label.pack(side="left", anchor="center")

        # Статус подключения
        status_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        status_frame.pack(side="right")

        ping_label = ctk.CTkLabel(
            status_frame,
            text="--- мс",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        ping_label.pack(side="left", padx=5)

        players_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        )
        players_label.pack(side="left", padx=5)

        # IP адрес
        ip_label = ctk.CTkLabel(
            left_frame,
            text=f"{server.host}:{server.port}",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        ip_label.pack(anchor="w")

        # MOTD
        motd_label = ctk.CTkLabel(
            left_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray70"),
            wraplength=400,
            justify="left"
        )
        motd_label.pack(anchor="w", pady=(4, 0))

        # Правая часть: кнопки действий
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.pack(side="right", padx=15, pady=12)

        join_btn = ctk.CTkButton(
            right_frame,
            text=t("servers.join"),
            command=lambda s=server: self._connect_to_server(s),
            width=140,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        )
        join_btn.pack(side="left", padx=(0, 8))

        delete_btn = ctk.CTkButton(
            right_frame,
            text=t("servers.delete"),
            command=lambda s=server: self._delete_server(s),
            width=45,
            height=36,
            font=ctk.CTkFont(size=16),
            corner_radius=8,
            fg_color=("#c44040", "#dc4444"),
            hover_color=("#dc4444", "#f05050"),
            text_color=("#ffcdd2", "#ffcdd2")
        )
        delete_btn.pack(side="left")

        # Сохраняем ссылки на обновляемые виджеты
        self._server_widgets[server.name] = {
            "ping": ping_label,
            "motd": motd_label,
            "players": players_label,
        }

    def _refresh_all_servers(self) -> None:
        """Обновление информации о всех серверах (пинг, MOTD) в фоне."""
        def refresh() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                for server in self.server_manager.get_all_servers():
                    try:
                        status = loop.run_until_complete(
                            self.server_manager.refresh_server_info(server)
                        )
                        self.after(
                            0,
                            lambda s=server.name, st=status: self._update_server_ui(s, st),
                        )
                    except Exception:
                        pass
            finally:
                loop.close()

        threading.Thread(target=refresh, daemon=True).start()

    def _update_server_ui(self, server_name: str, status: ServerStatus) -> None:
        """Обновляет UI карточки сервера данными пинга."""
        widgets = self._server_widgets.get(server_name)
        if not widgets:
            return

        if status.online:
            ping_color = (
                "#1bd96a"
                if status.ping_ms < 100
                else "#f1c40f" if status.ping_ms < 200 else "#e74c3c"
            )
            widgets["ping"].configure(
                text=f"{status.ping_ms:.0f} мс",
                text_color=ping_color,
            )
            widgets["motd"].configure(text=status.motd or "")
            if status.players_max > 0:
                widgets["players"].configure(
                    text=f"{status.players_online}/{status.players_max}",
                    text_color="gray70"
                )
        else:
            widgets["ping"].configure(text="offline", text_color="#e74c3c")
            widgets["motd"].configure(text=status.error or "Нет ответа")

    def _add_server_dialog(self) -> None:
        """Открытие диалога добавления сервера."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить сервер")
        dialog.geometry("450x320")
        dialog.transient(self.controller)
        dialog.resizable(False, False)

        # Заголовок
        header_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(25, 15))

        title = ctk.CTkLabel(
            header_frame,
            text=t("servers.new_title"),
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(side="left")

        # Название
        name_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        name_frame.pack(fill="x", padx=30, pady=(10, 15))

        name_label = ctk.CTkLabel(
            name_frame,
            text=t("servers.name_label"),
            font=ctk.CTkFont(size=13, weight="bold")
        )
        name_label.pack(anchor="w")

        name_entry = ctk.CTkEntry(
            name_frame,
            placeholder_text="Hypixel",
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=8
        )
        name_entry.pack(fill="x", pady=(8, 0))

        # IP и порт
        ip_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        ip_frame.pack(fill="x", padx=30, pady=(15, 15))

        ip_label = ctk.CTkLabel(
            ip_frame,
            text=t("servers.ip_label"),
            font=ctk.CTkFont(size=13, weight="bold")
        )
        ip_label.pack(anchor="w")

        ip_entry = ctk.CTkEntry(
            ip_frame,
            placeholder_text="example.com",
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=8
        )
        ip_entry.pack(fill="x", pady=(8, 0))

        port_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        port_frame.pack(fill="x", padx=30, pady=(15, 20))

        port_label = ctk.CTkLabel(
            port_frame,
            text=t("servers.port_label"),
            font=ctk.CTkFont(size=13, weight="bold")
        )
        port_label.pack(anchor="w")

        port_frame_inner = ctk.CTkFrame(port_frame, fg_color="transparent")
        port_frame_inner.pack(fill="x")

        port_entry = ctk.CTkEntry(
            port_frame_inner,
            placeholder_text="25565",
            font=ctk.CTkFont(size=13),
            width=120,
            height=36,
            corner_radius=8
        )
        port_entry.pack(side="left")

        port_hint = ctk.CTkLabel(
            port_frame_inner,
            text=t("servers.port_hint"),
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        port_hint.pack(side="left", padx=(15, 0), pady=(10, 0))

        # Кнопки
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 25))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=t("servers.cancel"),
            command=dialog.destroy,
            width=120,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            fg_color="transparent",
            text_color=("#a0a0a0", "#d0d0d0"),
            hover_color=("#3a3a45", "#404050")
        )
        cancel_btn.pack(side="left", padx=5)

        save_btn = ctk.CTkButton(
            btn_frame,
            text=t("servers.save"),
            command=lambda: self._save_server_dialog(
                name_entry.get().strip(),
                ip_entry.get().strip(),
                port_entry.get().strip(),
                dialog
            ),
            width=120,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        )
        save_btn.pack(side="right", padx=5)

    def _save_server_dialog(self, name: str, host: str, port_text: str, dialog) -> None:
        """Сохраняет сервер из диалога."""
        if not name or not host:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все обязательные поля")
            return

        try:
            port = int(port_text) if port_text else 25565
        except ValueError:
            messagebox.showerror("Ошибка", "Порт должен быть числом")
            return

        self.server_manager.add_server(name, host, port)
        self._load_servers()
        dialog.destroy()

    def _connect_to_server(self, server: ServerInfo) -> None:
        """Подключение к серверу."""
        # TODO: Реализовать запуск Minecraft с подключением к серверу
        messagebox.showinfo(
            t("servers.join").replace("▶ ", ""),
            t("servers.connect_msg", name=server.name, host=server.host, port=server.port)
        )

    def _delete_server(self, server: ServerInfo) -> None:
        """Удаление сервера."""
        if messagebox.askyesno(
            t("servers.cancel"),
            t("servers.confirm_delete", name=server.name)
        ):
            self.server_manager.remove_server(server)
            self._load_servers()
