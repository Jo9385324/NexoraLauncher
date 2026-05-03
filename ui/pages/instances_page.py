"""Страница управления инстансами."""

from pathlib import Path

import customtkinter as ctk
from loguru import logger

from quantumlauncher.core.instance import Instance, InstanceManager
from quantumlauncher.core.pack_manager import export_instance, import_mrpack, import_zip


class InstancesPage(ctk.CTkFrame):
    """Страница инстансов (сборок)."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_content()
        self._load_instances()

    def _create_header(self) -> None:
        """Создаёт заголовок."""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header,
            text="Инстансы",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.import_btn = ctk.CTkButton(
            self.header,
            text="📥 Импорт",
            width=120,
            command=self._show_import_dialog,
        )
        self.import_btn.grid(row=0, column=1, padx=(10, 0))

        self.create_btn = ctk.CTkButton(
            self.header,
            text="➕ Создать",
            width=120,
            command=self._show_create_dialog,
        )
        self.create_btn.grid(row=0, column=2, padx=(10, 0))

    def _create_content(self) -> None:
        """Создаёт список инстансов."""
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=1, column=0, sticky="nsew")

    def _load_instances(self) -> None:
        """Загружает и отображает инстансы."""
        for widget in self.scroll.winfo_children():
            widget.destroy()

        instances = InstanceManager.list_instances()
        if not instances:
            label = ctk.CTkLabel(
                self.scroll,
                text="Нет созданных инстансов.\nНажмите 'Создать' для начала.",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            )
            label.pack(pady=40)
            return

        for instance in instances:
            self._add_instance_card(instance)

    def _add_instance_card(self, instance: Instance) -> None:
        """Добавляет карточку инстанса."""
        card = ctk.CTkFrame(self.scroll)
        card.pack(fill="x", pady=5, padx=5)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        name_lbl = ctk.CTkLabel(
            info,
            text=instance.name,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        name_lbl.pack(anchor="w")

        meta = f"{instance.mod_loader} {instance.version}"
        if instance.play_count > 0:
            meta += f"  •  Запусков: {instance.play_count}"
        meta_lbl = ctk.CTkLabel(info, text=meta, font=ctk.CTkFont(size=12), text_color="gray")
        meta_lbl.pack(anchor="w")

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(side="right", padx=10, pady=10)

        play_btn = ctk.CTkButton(
            btns,
            text="▶ Играть",
            width=80,
            height=28,
            command=lambda i=instance: self._play_instance(i),
        )
        play_btn.pack(side="left", padx=2)

        export_btn = ctk.CTkButton(
            btns,
            text="⬆",
            width=40,
            height=28,
            fg_color="transparent",
            command=lambda i=instance: self._export_instance(i),
        )
        export_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            btns,
            text="🗑",
            width=40,
            height=28,
            fg_color="transparent",
            hover_color=("#aa3333", "#aa3333"),
            text_color=("#cc4444", "#ff6666"),
            command=lambda n=instance.name: self._delete_instance(n),
        )
        del_btn.pack(side="left", padx=2)

    def _show_create_dialog(self) -> None:
        """Показывает диалог создания инстанса."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Создать инстанс")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Название:", font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=20, pady=(20, 5)
        )
        name_entry = ctk.CTkEntry(dialog, font=ctk.CTkFont(size=13))
        name_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(dialog, text="Версия Minecraft:", font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=20, pady=(10, 5)
        )
        version_entry = ctk.CTkEntry(dialog, placeholder_text="1.20.1", font=ctk.CTkFont(size=13))
        version_entry.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(dialog, text="Загрузчик:", font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=20, pady=(10, 5)
        )
        loader_var = ctk.StringVar(value="vanilla")
        loader_combo = ctk.CTkComboBox(
            dialog,
            values=["vanilla", "forge", "fabric", "quilt"],
            variable=loader_var,
            font=ctk.CTkFont(size=13),
        )
        loader_combo.pack(fill="x", padx=20, pady=(0, 20))

        def on_create() -> None:
            name = name_entry.get().strip()
            version = version_entry.get().strip()
            loader = loader_var.get()

            if not name or not version:
                return

            try:
                InstanceManager.create(name, version, loader)
                self.controller.set_status(f"Инстанс '{name}' создан")
                dialog.destroy()
                self._load_instances()
            except Exception as exc:
                logger.error("Ошибка создания инстанса: {}", exc)
                self.controller.set_status(f"Ошибка: {exc}")

        ctk.CTkButton(
            dialog,
            text="Создать",
            command=on_create,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=10)

    def _play_instance(self, instance: Instance) -> None:
        """Устанавливает инстанс для запуска."""
        self.controller.config.last_version = instance.version
        self.controller.config.save()
        self.controller.show_page("home")
        self.controller.set_status(f"Выбран инстанс: {instance.name}")

    def _delete_instance(self, name: str) -> None:
        """Удаляет инстанс после подтверждения."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Подтверждение")
        dialog.geometry("350x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f"Удалить инстанс '{name}'?\nЭто действие необратимо.",
            font=ctk.CTkFont(size=13),
        ).pack(pady=20)

        def confirm() -> None:
            InstanceManager.delete(name)
            dialog.destroy()
            self._load_instances()
            self.controller.set_status(f"Инстанс '{name}' удалён")

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(pady=10)

        ctk.CTkButton(btns, text="Отмена", command=dialog.destroy).pack(side="left", padx=5)
        ctk.CTkButton(
            btns,
            text="Удалить",
            fg_color="#cc4444",
            hover_color="#aa2222",
            command=confirm,
        ).pack(side="left", padx=5)

    def _export_instance(self, instance: Instance) -> None:
        """Экспортирует инстанс в .zip."""
        from tkinter import filedialog

        path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP архив", "*.zip")],
            initialfile=f"{instance.name}.zip",
        )
        if not path:
            return
        try:
            export_instance(instance, Path(path))
            self.controller.set_status(f"Экспорт '{instance.name}' завершён")
        except Exception as exc:
            logger.error("Ошибка экспорта: {}", exc)
            self.controller.set_status(f"❌ Ошибка экспорта: {exc}")

    def _show_import_dialog(self) -> None:
        """Показывает диалог импорта инстанса."""
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            filetypes=[
                ("Все поддерживаемые", "*.zip *.mrpack"),
                ("ZIP архив", "*.zip"),
                ("Modrinth pack", "*.mrpack"),
            ],
        )
        if not path:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Импорт инстанса")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Название нового инстанса:",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=20, pady=(20, 5))

        name_entry = ctk.CTkEntry(dialog, font=ctk.CTkFont(size=13))
        name_entry.pack(fill="x", padx=20, pady=(0, 10))
        name_entry.insert(0, Path(path).stem)

        status = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        status.pack(pady=5)

        def do_import() -> None:
            name = name_entry.get().strip()
            if not name:
                status.configure(text="Введите название", text_color="red")
                return
            try:
                if path.endswith(".mrpack"):
                    import_mrpack(Path(path), name)
                else:
                    import_zip(Path(path), name)
                self.controller.set_status(f"Инстанс '{name}' импортирован")
                dialog.destroy()
                self._load_instances()
            except Exception as exc:
                logger.error("Ошибка импорта: {}", exc)
                status.configure(text=f"Ошибка: {exc}", text_color="red")

        ctk.CTkButton(
            dialog,
            text="Импортировать",
            command=do_import,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=10)
