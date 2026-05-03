"""Страница управления версиями."""

import threading

import customtkinter as ctk
from loguru import logger

from quantumlauncher.core.minecraft import MinecraftManager


class VersionsPage(ctk.CTkFrame):
    """Страница установки и управления версиями."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.mc_manager = MinecraftManager()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_tabs()
        self._load_versions()

    def _create_header(self) -> None:
        """Создаёт заголовок."""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self.title_label = ctk.CTkLabel(
            self.header,
            text="Управление версиями",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.pack(anchor="w")

    def _create_tabs(self) -> None:
        """Создаёт вкладки."""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.installed_tab = self.tabview.add("Установленные")
        self.available_tab = self.tabview.add("Доступные")

        self._create_installed_tab()
        self._create_available_tab()

    def _create_installed_tab(self) -> None:
        """Создаёт содержимое вкладки установленных версий."""
        self.installed_tab.grid_columnconfigure(0, weight=1)
        self.installed_tab.grid_rowconfigure(0, weight=1)

        self.installed_list = ctk.CTkScrollableFrame(self.installed_tab)
        self.installed_list.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.refresh_installed_btn = ctk.CTkButton(
            self.installed_tab,
            text="🔄 Обновить",
            command=self._load_installed_versions,
        )
        self.refresh_installed_btn.grid(row=1, column=0, padx=10, pady=(0, 10))

    def _create_available_tab(self) -> None:
        """Создаёт содержимое вкладки доступных версий."""
        self.available_tab.grid_columnconfigure(0, weight=1)
        self.available_tab.grid_rowconfigure(1, weight=1)

        self.filter_frame = ctk.CTkFrame(self.available_tab, fg_color="transparent")
        self.filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.filter_var = ctk.StringVar(value="all")
        self.filter_release = ctk.CTkRadioButton(
            self.filter_frame,
            text="Релизы",
            variable=self.filter_var,
            value="release",
            command=self._filter_versions,
        )
        self.filter_release.pack(side="left", padx=5)

        self.filter_snapshot = ctk.CTkRadioButton(
            self.filter_frame,
            text="Снапшоты",
            variable=self.filter_var,
            value="snapshot",
            command=self._filter_versions,
        )
        self.filter_snapshot.pack(side="left", padx=5)

        self.filter_all = ctk.CTkRadioButton(
            self.filter_frame,
            text="Все",
            variable=self.filter_var,
            value="all",
            command=self._filter_versions,
        )
        self.filter_all.pack(side="left", padx=5)

        self.available_list = ctk.CTkScrollableFrame(self.available_tab)
        self.available_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.progress = ctk.CTkProgressBar(self.available_tab, mode="indeterminate")
        self.progress.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progress.set(0)

    def _load_versions(self) -> None:
        """Загружает списки версий."""
        self._load_installed_versions()
        self._load_available_versions()

    def _load_installed_versions(self) -> None:
        """Загружает установленные версии."""
        for widget in self.installed_list.winfo_children():
            widget.destroy()

        try:
            versions = self.mc_manager.get_installed_versions()
            if not versions:
                label = ctk.CTkLabel(
                    self.installed_list,
                    text="Нет установленных версий",
                    font=ctk.CTkFont(size=14),
                    text_color="gray",
                )
                label.pack(pady=20)
                return

            for version in versions:
                self._add_version_row(self.installed_list, version["id"], installed=True)
        except Exception as e:
            logger.error("Ошибка загрузки установленных версий: {}", e)
            label = ctk.CTkLabel(
                self.installed_list,
                text=f"Ошибка загрузки: {e}",
                text_color="red",
            )
            label.pack(pady=20)

    def _load_available_versions(self) -> None:
        """Загружает доступные версии в фоне."""
        self.progress.start()
        self.controller.set_status("Загрузка списка версий...")

        def load() -> None:
            try:
                self.all_versions = self.mc_manager.get_available_versions()
                self.after(0, self._render_available_versions)
            except Exception as exc:
                logger.error("Ошибка загрузки версий: {}", exc)
                self.after(0, lambda err=str(exc): self.controller.set_status(f"Ошибка: {err}"))
            finally:
                self.after(0, self.progress.stop)

        threading.Thread(target=load, daemon=True).start()

    def _render_available_versions(self) -> None:
        """Отрисовывает список доступных версий."""
        for widget in self.available_list.winfo_children():
            widget.destroy()

        filter_type = self.filter_var.get()
        versions = self.all_versions

        if filter_type != "all":
            versions = [v for v in versions if v["type"] == filter_type]

        for version in versions[:50]:  # Ограничиваем для производительности
            self._add_version_row(
                self.available_list,
                version["id"],
                installed=False,
                version_type=version["type"],
            )

        self.controller.set_status(f"Загружено {len(versions)} версий")

    def _filter_versions(self) -> None:
        """Фильтрует версии по типу."""
        self._render_available_versions()

    def _add_version_row(
        self,
        parent: ctk.CTkScrollableFrame,
        version_id: str,
        installed: bool,
        version_type: str = "",
    ) -> None:
        """Добавляет строку версии в список."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)

        type_color = "green" if version_type == "release" else "orange"
        type_text = f" [{version_type}]" if version_type else ""

        label = ctk.CTkLabel(
            row,
            text=f"{version_id}{type_text}",
            font=ctk.CTkFont(size=13),
            text_color=type_color if version_type else None,
        )
        label.pack(side="left", padx=5)

        btns = ctk.CTkFrame(row, fg_color="transparent")
        btns.pack(side="right")

        if installed:
            ctk.CTkButton(
                btns,
                text="▶",
                width=40,
                height=28,
                command=lambda vid=version_id: self._play_version(vid),
            ).pack(side="left", padx=1)
            # Forge/Fabric только для vanilla
            if "forge" not in version_id and "fabric" not in version_id:
                ctk.CTkButton(
                    btns,
                    text="Forge",
                    width=50,
                    height=28,
                    font=ctk.CTkFont(size=11),
                    command=lambda vid=version_id: self._install_forge(vid),
                ).pack(side="left", padx=1)
                ctk.CTkButton(
                    btns,
                    text="Fabric",
                    width=50,
                    height=28,
                    font=ctk.CTkFont(size=11),
                    command=lambda vid=version_id: self._install_fabric(vid),
                ).pack(side="left", padx=1)
        else:
            ctk.CTkButton(
                btns,
                text="Vanilla",
                width=60,
                height=28,
                font=ctk.CTkFont(size=11),
                command=lambda vid=version_id: self._install_version(vid),
            ).pack(side="left", padx=1)
            ctk.CTkButton(
                btns,
                text="Forge",
                width=50,
                height=28,
                font=ctk.CTkFont(size=11),
                command=lambda vid=version_id: self._install_forge(vid),
            ).pack(side="left", padx=1)
            ctk.CTkButton(
                btns,
                text="Fabric",
                width=50,
                height=28,
                font=ctk.CTkFont(size=11),
                command=lambda vid=version_id: self._install_fabric(vid),
            ).pack(side="left", padx=1)

    def _play_version(self, version_id: str) -> None:
        """Устанавливает версию для запуска на главной."""
        self.controller.config.last_version = version_id
        self.controller.config.save()
        self.controller.show_page("home")
        self.controller.set_status(f"Версия {version_id} выбрана для запуска")

    def _install_version(self, version_id: str) -> None:
        """Устанавливает Vanilla версию с отображением прогресса."""
        self._run_install(version_id, self.mc_manager.install_version, "Vanilla")

    def _install_forge(self, version_id: str) -> None:
        """Устанавливает Forge для версии."""
        self._run_install(version_id, self.mc_manager.install_forge, "Forge")

    def _install_fabric(self, version_id: str) -> None:
        """Устанавливает Fabric для версии."""
        self._run_install(version_id, self.mc_manager.install_fabric, "Fabric")

    def _run_install(
        self,
        version_id: str,
        install_fn,
        label: str,
    ) -> None:
        """Универсальный метод установки с прогрессом."""
        self.controller.set_status(f"Установка {label} {version_id}...")
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        self.progress.start()

        def set_status(text: str) -> None:
            self.after(0, lambda: self.controller.set_status(text))

        def set_progress(progress: int) -> None:
            self.after(0, lambda: self.progress.set(progress / 100))

        callback = {
            "setStatus": set_status,
            "setProgress": set_progress,
        }

        def install() -> None:
            try:
                result = install_fn(version_id, callback=callback)
                installed_id = result if isinstance(result, str) else version_id
                self.after(0, lambda: self.controller.set_status(
                    f"✅ {label} {installed_id} установлен"
                ))
                self.after(0, self._load_installed_versions)
            except Exception as exc:
                logger.error("Ошибка установки {} {}: {}", label, version_id, exc)
                self.after(0, lambda err=str(exc): self.controller.set_status(
                    f"❌ Ошибка {label}: {err}"
                ))
            finally:
                self.after(0, self.progress.stop)
                self.after(0, lambda: self.progress.configure(mode="indeterminate"))

        threading.Thread(target=install, daemon=True).start()
