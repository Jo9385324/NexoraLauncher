"""Главная страница с запуском."""

import threading
from typing import Any

import customtkinter as ctk
from loguru import logger
from PIL import ImageTk

from quantumlauncher.core.auth import AuthManager
from quantumlauncher.core.crash_analyzer import analyze_latest_crash
from quantumlauncher.core.minecraft import MinecraftManager
from quantumlauncher.core.skin import SkinManager


class HomePage(ctk.CTkFrame):
    """Главная страница лаунчера."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.mc_manager = MinecraftManager()
        self.auth_manager = AuthManager()
        self.skin_manager = SkinManager()
        self._skin_photo: ImageTk.PhotoImage | None = None
        self._skin_after_id: str | None = None
        self._closed = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_launch_section()
        self._create_news_section()

    def destroy(self) -> None:
        self._closed = True
        if self._skin_after_id is not None:
            try:
                self.after_cancel(self._skin_after_id)
            except Exception:
                pass
        super().destroy()

    def _safe_after(self, ms: int, callback: Any) -> Any:
        """Безопасный вызов after с проверкой существования виджета."""
        if self._closed or not self.winfo_exists():
            return None
        return self.after(ms, callback)

    def _run_safe(self, fn: Any) -> None:
        """Безопасно выполняет функцию, если виджет ещё жив."""
        if self._closed or not self.winfo_exists():
            return
        try:
            fn()
        except Exception as exc:
            logger.debug("Ошибка в _run_safe: {}", exc)

    def _create_header(self) -> None:
        """Создаёт заголовок."""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(10, 15))

        # Заголовок с градиентным эффектом (упрощённый)
        welcome_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        welcome_frame.pack(fill="x")

        self.title_label = ctk.CTkLabel(
            welcome_frame,
            text="Добро пожаловать в QuantumLauncher",
            font=ctk.CTkFont(size=30, weight="bold"),
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            welcome_frame,
            text="Следующее поколение Minecraft лаунчера с расширенными возможностями",
            font=ctk.CTkFont(size=15),
            text_color="gray",
        )
        self.subtitle_label.pack(anchor="w", pady=(6, 0))

    def _create_launch_section(self) -> None:
        """Создаёт секцию запуска."""
        self.launch_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=("#323241", "#2d2d3c"),
            border_width=1,
            border_color=("#505064", "#46465a"),
        )
        self.launch_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        self.launch_frame.grid_columnconfigure(1, weight=1)

        section_header = ctk.CTkFrame(self.launch_frame, fg_color="transparent")
        section_header.grid(row=0, column=0, columnspan=2, padx=30, pady=(25, 15), sticky="w")

        section_title = ctk.CTkLabel(
            section_header,
            text="🚀 Запуск игры",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        section_title.pack(side="left")

        self.auth_label = ctk.CTkLabel(
            self.launch_frame,
            text="Тип авторизации:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.auth_label.grid(row=1, column=0, padx=30, pady=(10, 5), sticky="w")

        self.auth_var = ctk.StringVar(value="offline")
        auth_btns = ctk.CTkFrame(self.launch_frame, fg_color="transparent")
        auth_btns.grid(row=1, column=1, padx=30, pady=(10, 5), sticky="w")

        ctk.CTkRadioButton(
            auth_btns,
            text="Офлайн",
            variable=self.auth_var,
            value="offline",
            command=self._on_auth_change,
            font=ctk.CTkFont(size=13),
            radiobutton_width=18,
        ).pack(side="left", padx=5)
        ctk.CTkRadioButton(
            auth_btns,
            text="Microsoft",
            variable=self.auth_var,
            value="microsoft",
            command=self._on_auth_change,
            font=ctk.CTkFont(size=13),
            radiobutton_width=18,
        ).pack(side="left", padx=15)

        self.ms_id_label = ctk.CTkLabel(
            self.launch_frame,
            text="MS Client ID:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.ms_id_label.grid(row=2, column=0, padx=30, pady=(15, 5), sticky="w")
        self.ms_id_label.grid_remove()

        self.ms_id_entry = ctk.CTkEntry(
            self.launch_frame,
            placeholder_text="Вставьте Client ID",
            font=ctk.CTkFont(size=13),
            height=38,
            corner_radius=10,
        )
        self.ms_id_entry.grid(row=2, column=1, padx=30, pady=(15, 5), sticky="ew")
        self.ms_id_entry.grid_remove()
        if self.controller.config.ms_client_id:
            self.ms_id_entry.insert(0, self.controller.config.ms_client_id)

        self.ms_login_btn = ctk.CTkButton(
            self.launch_frame,
            text="🔑 Войти через Microsoft",
            command=self._on_ms_login,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10,
        )
        self.ms_login_btn.grid(row=3, column=0, columnspan=2, padx=30, pady=(5, 15))
        self.ms_login_btn.grid_remove()

        self.username_label = ctk.CTkLabel(
            self.launch_frame,
            text="Имя пользователя:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.username_label.grid(row=4, column=0, padx=30, pady=(10, 5), sticky="w")

        username_row = ctk.CTkFrame(self.launch_frame, fg_color="transparent")
        username_row.grid(row=4, column=1, padx=30, pady=(10, 5), sticky="ew")
        username_row.grid_columnconfigure(0, weight=1)

        self.username_entry = ctk.CTkEntry(
            username_row,
            placeholder_text="Введите имя",
            font=ctk.CTkFont(size=13),
            height=38,
            corner_radius=10,
        )
        self.username_entry.grid(row=0, column=0, sticky="ew")
        if self.controller.config.last_username:
            self.username_entry.insert(0, self.controller.config.last_username)

        self.skin_label = ctk.CTkLabel(username_row, text="", width=40)
        self.skin_label.grid(row=0, column=1, padx=(10, 0))

        # Debounce: обновляем скин через 300мс после ввода
        self.username_entry.bind("<KeyRelease>", lambda _e: self._schedule_skin_update())
        self.username_entry.bind("<FocusOut>", lambda _e: self._schedule_skin_update())
        self.username_entry.bind("<Return>", lambda _e: self._schedule_skin_update())
        if self.controller.config.last_username:
            self.after(100, self._update_skin_preview)

        self.version_label = ctk.CTkLabel(
            self.launch_frame,
            text="Версия игры:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.version_label.grid(row=5, column=0, padx=30, pady=(15, 5), sticky="w")

        self.version_var = ctk.StringVar(value=self.controller.config.last_version or "")
        self.version_combo = ctk.CTkComboBox(
            self.launch_frame,
            variable=self.version_var,
            values=self._get_installed_versions(),
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            height=40,
            corner_radius=10,
        )
        self.version_combo.grid(row=5, column=1, padx=30, pady=(15, 5), sticky="ew")

        self.ms_status = ctk.CTkLabel(
            self.launch_frame,
            text="",
            font=ctk.CTkFont(size=13),
        )
        self.ms_status.grid(row=6, column=0, columnspan=2, padx=30, pady=5)
        self.ms_status.grid_remove()

        self.launch_button = ctk.CTkButton(
            self.launch_frame,
            text="▶  Запустить Minecraft",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=55,
            command=self._on_launch,
            corner_radius=12,
        )
        self.launch_button.grid(row=7, column=0, columnspan=2, padx=30, pady=(15, 25))

        self._check_saved_ms_profile()

    def _create_news_section(self) -> None:
        """Создаёт секцию новостей/информации."""
        self.news_frame = ctk.CTkFrame(
            self,
            corner_radius=15,
            fg_color=("#323241", "#2d2d3c"),
            border_width=1,
            border_color=("#505064", "#46465a")
        )
        self.news_frame.grid(row=2, column=0, sticky="nsew")

        # Заголовок секции
        news_header = ctk.CTkFrame(self.news_frame, fg_color="transparent")
        news_header.pack(fill="x", padx=30, pady=(25, 15))

        self.news_label = ctk.CTkLabel(
            news_header,
            text="📰  Последние обновления",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.news_label.pack(side="left")

        # Метка "новое"
        new_badge = ctk.CTkLabel(
            news_header,
            text="НОВОЕ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="white",
            fg_color="#e74c3c",
            corner_radius=5,
            width=50,
            height=20
        )
        new_badge.pack(side="right")

        self.news_content = ctk.CTkLabel(
            self.news_frame,
            text="• QuantumLauncher v0.1.0 запущен!\n"
                 "• Добавлена поддержка Vanilla Minecraft\n"
                 "• Установка Forge и Fabric в разработке\n"
                 "• AI помощник скоро будет доступен",
            font=ctk.CTkFont(size=13),
            justify="left",
            text_color=("gray90", "gray85"),
            wraplength=600
        )
        self.news_content.pack(anchor="w", padx=30, pady=(0, 25))

    def _schedule_skin_update(self) -> None:
        """Откладывает обновление скина на 300 мс (debounce)."""
        if self._skin_after_id is not None:
            try:
                self.after_cancel(self._skin_after_id)
            except Exception:
                pass
        self._skin_after_id = self.after(300, self._update_skin_preview)

    def _update_skin_preview(self) -> None:
        """Обновляет превью скина по имени пользователя."""
        self._skin_after_id = None
        if self._closed or not self.winfo_exists():
            return

        username = self.username_entry.get().strip()
        if not username:
            return

        def load() -> None:
            try:
                skin_img = self.skin_manager.get_skin_image(username)
                if skin_img:
                    head = self.skin_manager.render_head(skin_img, scale=4)
                    tk_img = ImageTk.PhotoImage(head)
                    self._skin_photo = tk_img
                    self._safe_after(
                        0, lambda: self._run_safe(
                            lambda: self.skin_label.configure(image=tk_img)
                        )
                    )
                else:
                    self._safe_after(
                        0, lambda: self._run_safe(
                            lambda: self.skin_label.configure(image="")
                        )
                    )
            except Exception as exc:
                logger.debug("Не удалось загрузить скин {}: {}", username, exc)
                self._safe_after(
                    0, lambda: self._run_safe(
                        lambda: self.skin_label.configure(image="")
                    )
                )

        threading.Thread(target=load, daemon=True).start()

    def _on_auth_change(self) -> None:
        """Переключает UI при смене типа авторизации."""
        is_ms = self.auth_var.get() == "microsoft"
        if is_ms:
            self.ms_id_label.grid()
            self.ms_id_entry.grid()
            self.ms_login_btn.grid()
            self.username_label.grid_remove()
            self.username_entry.grid_remove()
            self._check_saved_ms_profile()
        else:
            self.ms_id_label.grid_remove()
            self.ms_id_entry.grid_remove()
            self.ms_login_btn.grid_remove()
            self.ms_status.grid_remove()
            self.username_label.grid()
            self.username_entry.grid()

    def _check_saved_ms_profile(self) -> None:
        """Проверяет наличие сохранённого MS профиля."""
        profile = self.auth_manager.load_saved_profile()
        if profile and profile.auth_type == "microsoft":
            self.ms_status.configure(
                text=f"✅ Сохранён профиль: {profile.username}",
                text_color="green",
            )
            self.ms_status.grid()
            self.ms_login_btn.configure(text="🔄 Обновить вход")

    def _on_ms_login(self) -> None:
        """Запускает MS OAuth flow."""
        client_id = self.ms_id_entry.get().strip()
        if not client_id:
            self.controller.set_status("❌ Введите MS Client ID")
            return

        self.controller.config.ms_client_id = client_id
        self.controller.config.save()

        try:
            login_data = self.auth_manager.microsoft_login_start(client_id)
            self.auth_manager.open_browser(login_data["url"])
            self.ms_status.configure(
                text="🌐 Браузер открыт. После входа вставьте код.",
                text_color="blue",
            )
            self.ms_status.grid()
            self._show_ms_code_dialog(client_id, login_data["code_verifier"])
        except Exception as exc:
            logger.error("Ошибка MS входа: {}", exc)
            self.controller.set_status(f"❌ Ошибка: {exc}")

    def _show_ms_code_dialog(self, client_id: str, code_verifier: str) -> None:
        """Диалог для ввода auth кода из браузера."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Microsoft Авторизация")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Вставьте URL или код из браузера:",
            font=ctk.CTkFont(size=13),
        ).pack(pady=(20, 5))

        code_entry = ctk.CTkEntry(dialog, font=ctk.CTkFont(size=12))
        code_entry.pack(fill="x", padx=20, pady=5)

        status = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        status.pack(pady=5)

        def on_confirm() -> None:
            raw = code_entry.get().strip()
            if not raw:
                return
            try:
                # Пытаемся извлечь код из URL
                auth_code = self.auth_manager._extract_auth_code(raw)
                profile = self.auth_manager.microsoft_login_complete(
                    client_id, auth_code, code_verifier
                )
                status.configure(
                    text=f"✅ Успех: {profile.username}",
                    text_color="green",
                )
                dialog.after(1000, dialog.destroy)
                self._check_saved_ms_profile()
            except Exception as exc:
                status.configure(text=f"❌ Ошибка: {exc}", text_color="red")

        ctk.CTkButton(dialog, text="Подтвердить", command=on_confirm).pack(pady=10)

    def _get_installed_versions(self) -> list[str]:
        """Возвращает список установленных версий."""
        try:
            versions = self.mc_manager.get_installed_versions()
            return [v["id"] for v in versions] if versions else ["Нет установленных версий"]
        except Exception as e:
            logger.error("Ошибка получения версий: {}", e)
            return ["Ошибка загрузки"]

    def _on_launch(self) -> None:
        """Обработчик запуска."""
        version = self.version_var.get()
        if not version or version in ("Нет установленных версий", "Ошибка загрузки"):
            self.controller.set_status("❌ Выберите версию")
            return

        self.controller.config.last_version = version
        self.controller.config.save()

        auth_type = self.auth_var.get()

        try:
            if auth_type == "microsoft":
                self._launch_microsoft(version)
            else:
                self._launch_offline(version)
        except Exception as e:
            self.controller.set_status(f"❌ Ошибка запуска: {e}")
            logger.exception("Ошибка запуска Minecraft")

    def _launch_offline(self, version: str) -> None:
        """Запуск с офлайн авторизацией."""
        username = self.username_entry.get().strip()
        if not username:
            self.controller.set_status("❌ Введите имя пользователя")
            return

        self.controller.config.last_username = username
        self.controller.config.save()

        self.controller.set_status(f"🚀 Запуск Minecraft {version}...")
        logger.info("Запуск {} для {}", version, username)

        profile = self.auth_manager.offline_login(username)
        process = self.mc_manager.launch(
            version_id=version,
            username=profile.username,
            java_path=self.controller.config.java_path,
            jvm_profile=self.controller.config.jvm_profile,
            max_memory=self.controller.config.max_memory,
            min_memory=self.controller.config.min_memory,
        )
        self.controller.set_status(f"✅ Minecraft запущен (PID: {process.pid})")
        logger.info("Minecraft запущен, PID: {}", process.pid)
        self.controller.discord_rpc.update_playing(version)
        self._monitor_process(process, version)

    def _monitor_process(self, process, version: str) -> None:
        """Мониторит процесс Minecraft и анализирует краш при нештатном завершении."""

        def watch() -> None:
            try:
                returncode = process.wait()
                self.controller.discord_rpc.update_launcher()
                if returncode != 0:
                    logger.warning("Minecraft завершился с кодом {}", returncode)
                    report = analyze_latest_crash(self.mc_manager.minecraft_dir)
                    if report:
                        msg = f"💥 {report.cause}: {report.suggestion}"
                        self._safe_after(
                            0, lambda: self._run_safe(
                                lambda: self.controller.set_status(msg)
                            )
                        )
                        self._safe_after(
                            0, lambda: self._run_safe(
                                lambda: self._show_crash_dialog(report)
                            )
                        )
                    else:
                        self._safe_after(
                            0,
                            lambda: self._run_safe(
                                lambda: self.controller.set_status(
                                    f"⚠️ Minecraft закрыт с ошибкой (код {returncode})"
                                )
                            ),
                        )
                else:
                    self._safe_after(
                        0, lambda: self._run_safe(
                            lambda: self.controller.set_status("👋 Minecraft закрыт")
                        )
                    )
            except Exception as exc:
                logger.debug("Ошибка мониторинга процесса: {}", exc)

        threading.Thread(target=watch, daemon=True).start()

    def _show_crash_dialog(self, report: Any) -> None:
        """Показывает диалог с результатами анализа краша."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Анализ краша")
        dialog.geometry("500x300")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f"💥 {report.cause}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="red" if report.severity == "critical" else "orange",
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            dialog,
            text=report.description,
            font=ctk.CTkFont(size=12),
            wraplength=460,
        ).pack(pady=5)

        ctk.CTkLabel(
            dialog,
            text=f"💡 {report.suggestion}",
            font=ctk.CTkFont(size=12),
            wraplength=460,
            justify="left",
        ).pack(pady=5)

        if report.raw_summary:
            summary = ctk.CTkTextbox(dialog, height=80, font=ctk.CTkFont(size=11))
            summary.pack(fill="x", padx=20, pady=5)
            summary.insert("0.0", report.raw_summary)
            summary.configure(state="disabled")

        ctk.CTkButton(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

    def _launch_microsoft(self, version: str) -> None:
        """Запуск с Microsoft авторизацией."""
        client_id = self.controller.config.ms_client_id
        if not client_id:
            self.controller.set_status("❌ Сначала выполните вход в Microsoft")
            return

        self.controller.set_status("🔄 Проверка Microsoft профиля...")

        profile = self.auth_manager.load_saved_profile()
        if profile and profile.refresh_token:
            try:
                profile = self.auth_manager.microsoft_refresh(client_id, profile.refresh_token)
            except Exception as exc:
                logger.warning("Не удалось обновить токен: {}", exc)
                self.controller.set_status("❌ Сессия истекла. Войдите снова.")
                return
        else:
            self.controller.set_status("❌ Сначала выполните вход в Microsoft")
            return

        self.controller.set_status(f"🚀 Запуск Minecraft {version}...")
        logger.info("Запуск {} для {} (MS)", version, profile.username)

        options = {
            "username": profile.username,
            "uuid": profile.uuid,
            "accessToken": profile.access_token,
        }
        process = self.mc_manager.launch(
            version_id=version,
            username=profile.username,
            options=options,
            java_path=self.controller.config.java_path,
            jvm_profile=self.controller.config.jvm_profile,
            max_memory=self.controller.config.max_memory,
            min_memory=self.controller.config.min_memory,
        )
        self.controller.set_status(f"✅ Minecraft запущен (PID: {process.pid})")
        logger.info("Minecraft запущен, PID: {}", process.pid)
        self.controller.discord_rpc.update_playing(version)
        self._monitor_process(process, version)
