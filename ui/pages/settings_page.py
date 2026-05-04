"""Страница настроек."""

import customtkinter as ctk
from loguru import logger

from quantumlauncher.core.java_detector import find_all_java
from quantumlauncher.core.jvm_flags import JvmProfile, get_profile_description
from quantumlauncher.utils.i18n import t


class SettingsPage(ctk.CTkFrame):
    """Страница настроек лаунчера."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_settings_form()

    def _create_header(self) -> None:
        """Создаёт заголовок."""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self.title_label = ctk.CTkLabel(
            self.header,
            text=t("settings.title"),
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.pack(anchor="w")

    def _create_settings_form(self) -> None:
        """Создаёт форму настроек."""
        self.form_frame = ctk.CTkScrollableFrame(self)
        self.form_frame.grid(row=1, column=0, sticky="nsew")

        config = self.controller.config

        # Java путь с автоопределением
        self._create_java_row(self.form_frame, config)

        # Максимальная память
        self._create_setting_row(
            self.form_frame,
            t("settings.memory") + " (max):",
            ctk.CTkEntry,
            value=str(config.max_memory),
            attr="max_memory",
        )

        # Минимальная память
        self._create_setting_row(
            self.form_frame,
            t("settings.memory") + " (min):",
            ctk.CTkEntry,
            value=str(config.min_memory),
            attr="min_memory",
        )

        # Тема
        self._create_combo_row(
            self.form_frame,
            t("settings.appearance") + ":",
            values=["dark", "light", "system"],
            current=config.appearance_mode,
            attr="appearance_mode",
        )

        # Цветовая схема
        self._create_combo_row(
            self.form_frame,
            t("settings.appearance") + " (color):",
            values=["blue", "green", "dark-blue"],
            current=config.color_theme,
            attr="color_theme",
        )

        # Профиль JVM
        jvm_values = [JvmProfile.DEFAULT, JvmProfile.PERFORMANCE, JvmProfile.LOW]
        jvm_display = [get_profile_description(v) for v in jvm_values]
        self._jvm_profile_map = dict(zip(jvm_display, jvm_values))
        self._jvm_profile_reverse = dict(zip(jvm_values, jvm_display))

        self._create_combo_row(
            self.form_frame,
            t("settings.jvm_profile") + ":",
            values=jvm_display,
            current=self._jvm_profile_reverse.get(config.jvm_profile, jvm_display[0]),
            attr="jvm_profile_display",
        )

        # Кнопка сохранения
        self.save_btn = ctk.CTkButton(
            self.form_frame,
            text=t("settings.save"),
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._save_settings,
        )
        self.save_btn.pack(fill="x", padx=10, pady=20)

    def _create_setting_row(
        self,
        parent: ctk.CTkScrollableFrame,
        label: str,
        widget_cls: type,
        value: str,
        attr: str,
    ) -> None:
        """Создаёт строку настройки с label + entry."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5, padx=10)

        lbl = ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=13), width=150)
        lbl.pack(side="left")

        entry = widget_cls(row, font=ctk.CTkFont(size=13))
        entry.insert(0, value)
        entry.pack(side="right", fill="x", expand=True, padx=(10, 0))

        setattr(self, f"_{attr}_widget", entry)

    def _create_combo_row(
        self,
        parent: ctk.CTkScrollableFrame,
        label: str,
        values: list[str],
        current: str,
        attr: str,
    ) -> None:
        """Создаёт строку настройки с combobox."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5, padx=10)

        lbl = ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=13), width=150)
        lbl.pack(side="left")

        var = ctk.StringVar(value=current)
        combo = ctk.CTkComboBox(
            row,
            values=values,
            variable=var,
            font=ctk.CTkFont(size=13),
        )
        combo.pack(side="right", fill="x", expand=True, padx=(10, 0))

        setattr(self, f"_{attr}_widget", combo)

    def _create_java_row(self, parent: ctk.CTkScrollableFrame, config) -> None:
        """Создаёт строку выбора Java с автоопределением."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=5, padx=10)

        lbl = ctk.CTkLabel(
            row, text=t("settings.java_path") + ":", font=ctk.CTkFont(size=13), width=150
        )
        lbl.pack(side="left")

        self._java_path_widget = ctk.CTkEntry(row, font=ctk.CTkFont(size=13))
        self._java_path_widget.insert(0, config.java_path or "")
        self._java_path_widget.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self._java_detect_btn = ctk.CTkButton(
            row,
            text=t("settings.java_auto"),
            width=80,
            command=self._on_detect_java,
        )
        self._java_detect_btn.pack(side="left", padx=(5, 0))

        # Выпадающий список найденных Java (изначально скрыт)
        self._java_combo = ctk.CTkComboBox(
            parent,
            values=[],
            font=ctk.CTkFont(size=12),
            command=self._on_java_selected,
        )
        self._java_combo.pack(fill="x", padx=10, pady=(0, 5))
        self._java_combo.pack_forget()

    def _on_detect_java(self) -> None:
        """Запускает автоопределение Java."""
        self.controller.set_status(t("settings.java_auto") + " ...")
        self._java_detect_btn.configure(state="disabled")

        def detect() -> None:
            try:
                java_list = find_all_java()
                self.after(0, lambda: self._show_java_results(java_list))
            except Exception as exc:
                logger.error("Ошибка поиска Java: {}", exc)
                msg = str(exc)
                self.after(0, lambda: self.controller.set_status(f"❌ Ошибка: {msg}"))
            finally:
                self.after(0, lambda: self._java_detect_btn.configure(state="normal"))

        import threading

        threading.Thread(target=detect, daemon=True).start()

    def _show_java_results(self, java_list: list) -> None:
        """Показывает найденные Java в выпадающем списке."""
        if not java_list:
            self.controller.set_status(t("settings.java_not_found"))
            return

        self._java_options = {}
        display_values = []
        for info in java_list:
            label = f"{info.version} ({info.vendor}) — {info.path.parent.parent}"
            display_values.append(label)
            self._java_options[label] = str(info.path)

        self._java_combo.configure(values=display_values)
        self._java_combo.set(display_values[0])
        self._java_combo.pack(fill="x", padx=10, pady=(0, 5))

        # сразу подставляем первую
        self._java_path_widget.delete(0, "end")
        self._java_path_widget.insert(0, self._java_options[display_values[0]])

        self.controller.set_status(t("settings.java_found", count=len(java_list)))

    def _on_java_selected(self, choice: str) -> None:
        """Обработчик выбора Java из списка."""
        path = self._java_options.get(choice, "")
        self._java_path_widget.delete(0, "end")
        self._java_path_widget.insert(0, path)

    def _save_settings(self) -> None:
        """Сохраняет настройки."""
        try:
            config = self.controller.config

            config.java_path = self._get_widget_value("java_path")
            config.max_memory = int(self._get_widget_value("max_memory"))
            config.min_memory = int(self._get_widget_value("min_memory"))
            config.appearance_mode = self._get_widget_value("appearance_mode")
            config.color_theme = self._get_widget_value("color_theme")

            display_profile = self._get_widget_value("jvm_profile_display")
            config.jvm_profile = self._jvm_profile_map.get(
                display_profile, JvmProfile.DEFAULT
            )

            config.save()

            # Применяем тему
            ctk.set_appearance_mode(config.appearance_mode)
            ctk.set_default_color_theme(config.color_theme)

            self.controller.set_status(t("settings.saved"))
            logger.info("Настройки сохранены")
        except Exception as e:
            self.controller.set_status(t("settings.save_error", error=e))
            logger.error("Ошибка сохранения настроек: {}", e)

    def _get_widget_value(self, attr: str) -> str:
        """Получает значение виджета по атрибуту."""
        widget = getattr(self, f"_{attr}_widget")
        value = widget.get()
        return str(value) if value is not None else ""
