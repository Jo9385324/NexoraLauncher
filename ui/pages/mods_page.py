"""Страница поиска и управления модами через Modrinth."""

import asyncio
import threading
from pathlib import Path

import customtkinter as ctk
from loguru import logger

from quantumlauncher.api.modrinth import ModrinthClient, ModrinthProject


class ModsPage(ctk.CTkFrame):
    """Страница модов с интеграцией Modrinth."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.client = ModrinthClient()
        self.results: list[ModrinthProject] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._create_search_bar()
        self._create_filters()
        self._create_results_list()
        self._create_status()

    def _create_search_bar(self) -> None:
        """Создаёт строку поиска."""
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Поиск модов на Modrinth...",
            font=ctk.CTkFont(size=14),
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda _e: self._on_search())

        self.search_btn = ctk.CTkButton(
            self.search_frame,
            text="🔍 Найти",
            width=100,
            command=self._on_search,
        )
        self.search_btn.grid(row=0, column=1)

    def _create_filters(self) -> None:
        """Создаёт фильтры поиска."""
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(self.filter_frame, text="Версия:", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 5)
        )
        self.version_filter = ctk.CTkEntry(
            self.filter_frame,
            placeholder_text="1.20.1",
            width=100,
            font=ctk.CTkFont(size=12),
        )
        self.version_filter.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(self.filter_frame, text="Загрузчик:", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 5)
        )
        self.loader_filter = ctk.CTkComboBox(
            self.filter_frame,
            values=["Любой", "fabric", "forge", "quilt", "neoforge"],
            width=120,
            font=ctk.CTkFont(size=12),
        )
        self.loader_filter.set("Любой")
        self.loader_filter.pack(side="left")

    def _create_results_list(self) -> None:
        """Создаёт список результатов."""
        self.results_frame = ctk.CTkScrollableFrame(self)
        self.results_frame.grid(row=2, column=0, sticky="nsew")

        self.placeholder = ctk.CTkLabel(
            self.results_frame,
            text="Введите запрос для поиска модов",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        self.placeholder.pack(pady=40)

    def _create_status(self) -> None:
        """Создаёт индикатор прогресса."""
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.progress.set(0)

    def _on_search(self) -> None:
        """Обработчик поиска."""
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_btn.configure(state="disabled")
        self.progress.start()
        self.controller.set_status(f"Поиск '{query}' на Modrinth...")

        def search() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self._do_search(query))
                self.after(0, lambda: self._show_results(results))
            except Exception as exc:
                logger.error("Ошибка поиска модов: {}", exc)
                self.after(
                    0,
                    lambda err=str(exc): self.controller.set_status(
                        f"Ошибка поиска: {err}"
                    ),
                )
            finally:
                loop.close()
                self.after(0, self.progress.stop)
                self.after(0, lambda: self.search_btn.configure(state="normal"))

        threading.Thread(target=search, daemon=True).start()

    async def _do_search(self, query: str) -> list[ModrinthProject]:
        """Выполняет асинхронный поиск."""
        async with self.client:
            facets: list[str] = []
            loader = self.loader_filter.get()
            if loader != "Любой":
                facets.append(f'["categories:{loader}"]')
            return await self.client.search(
                query, facets=facets if facets else None, limit=20
            )

    def _show_results(self, results: list[ModrinthProject]) -> None:
        """Отображает результаты поиска."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.results = results

        if not results:
            label = ctk.CTkLabel(
                self.results_frame,
                text="Ничего не найдено",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            )
            label.pack(pady=40)
            self.controller.set_status("Ничего не найдено")
            return

        for project in results:
            self._add_mod_card(project)

        self.controller.set_status(f"Найдено {len(results)} модов")

    def _add_mod_card(self, project: ModrinthProject) -> None:
        """Добавляет карточку мода."""
        card = ctk.CTkFrame(self.results_frame)
        card.pack(fill="x", pady=5, padx=5)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        title = ctk.CTkLabel(
            info,
            text=project.title,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        title.pack(anchor="w")

        desc_text = project.description
        if len(desc_text) > 120:
            desc_text = desc_text[:120] + "..."

        desc = ctk.CTkLabel(
            info,
            text=desc_text,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=500,
        )
        desc.pack(anchor="w")

        cats = " / ".join(project.categories[:3])
        meta = ctk.CTkLabel(
            info,
            text=f"⬇ {project.downloads:,}  •  {cats}",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
        )
        meta.pack(anchor="w", pady=(5, 0))

        btn = ctk.CTkButton(
            card,
            text="⬇ Установить",
            width=100,
            height=28,
            command=lambda p=project: self._show_mod_details(p),
        )
        btn.pack(side="right", padx=10, pady=10)

    def _show_mod_details(self, project: ModrinthProject) -> None:
        """Показывает диалог установки мода."""
        from quantumlauncher.core.instance import InstanceManager

        dialog = ctk.CTkToplevel(self)
        dialog.title(project.title)
        dialog.geometry("500x500")
        dialog.transient(self)
        dialog.grab_set()

        # Заголовок
        ctk.CTkLabel(
            dialog,
            text=project.title,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            dialog,
            text=project.description,
            font=ctk.CTkFont(size=12),
            wraplength=450,
            text_color="gray",
        ).pack(padx=20, pady=5)

        # Выбор инстанса
        ctk.CTkLabel(
            dialog, text="Инстанс:", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 5))

        instances = InstanceManager.list_instances()
        instance_names = [i.name for i in instances] if instances else ["Нет инстансов"]
        instance_var = ctk.StringVar(value=instance_names[0])
        instance_combo = ctk.CTkComboBox(
            dialog,
            values=instance_names,
            variable=instance_var,
            font=ctk.CTkFont(size=12),
        )
        instance_combo.pack(fill="x", padx=20, pady=(0, 10))

        # Версия игры
        ctk.CTkLabel(
            dialog, text="Версия Minecraft:", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        mc_versions = project.game_versions[:20] if project.game_versions else ["?"]
        mc_version_var = ctk.StringVar(value=mc_versions[0])
        mc_version_combo = ctk.CTkComboBox(
            dialog,
            values=mc_versions,
            variable=mc_version_var,
            font=ctk.CTkFont(size=12),
        )
        mc_version_combo.pack(fill="x", padx=20, pady=(0, 10))

        # Загрузчик
        ctk.CTkLabel(
            dialog, text="Загрузчик:", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        loaders = ["fabric", "forge", "quilt"]
        loader_var = ctk.StringVar(value="fabric")
        loader_combo = ctk.CTkComboBox(
            dialog,
            values=loaders,
            variable=loader_var,
            font=ctk.CTkFont(size=12),
        )
        loader_combo.pack(fill="x", padx=20, pady=(0, 15))

        # Статус установки
        status_label = ctk.CTkLabel(
            dialog, text="", font=ctk.CTkFont(size=12), text_color="gray"
        )
        status_label.pack(pady=5)

        def on_install() -> None:
            name = instance_var.get()
            if name == "Нет инстансов":
                status_label.configure(text="❌ Создайте инстанс сначала", text_color="red")
                return
            self._install_mod(
                project=project,
                instance_name=name,
                game_version=mc_version_var.get(),
                loader=loader_var.get(),
                dialog=dialog,
                status_label=status_label,
            )

        # Кнопки
        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(pady=15)

        ctk.CTkButton(btns, text="Закрыть", command=dialog.destroy).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            btns,
            text="⬇ Установить",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=on_install,
        ).pack(side="left", padx=5)

    def _install_mod(
        self,
        project: ModrinthProject,
        instance_name: str,
        game_version: str,
        loader: str,
        dialog: ctk.CTkToplevel,
        status_label: ctk.CTkLabel,
    ) -> None:
        """Скачивает и устанавливает мод в инстанс."""
        from quantumlauncher.core.instance import Instance

        instance = Instance.load(instance_name)
        if instance is None:
            status_label.configure(text="❌ Инстанс не найден", text_color="red")
            return

        status_label.configure(text="⏳ Поиск версии мода...", text_color="orange")
        dialog.update()

        def install() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def _do() -> str:
                    async with self.client:
                        version = await self.client.get_best_version(
                            project.project_id, game_version, loader
                        )
                        if version is None:
                            raise ValueError(
                                f"Нет версии для {game_version}/{loader}"
                            )
                        status_label.configure(
                            text=f"⬇ Скачивание {version.version_number}...",
                            text_color="blue",
                        )
                        dialog.update()
                        path = await self.client.download_mod(
                            version, str(instance.mods_dir)
                        )
                        return path

                result = loop.run_until_complete(_do())
                loop.close()
                self.after(
                    0,
                    lambda: status_label.configure(
                        text=f"✅ Установлен: {Path(result).name}", text_color="green"
                    ),
                )
                self.after(
                    0,
                    lambda: self.controller.set_status(
                        f"Мод {project.title} установлен в {instance_name}"
                    ),
                )
            except Exception as exc:
                logger.error("Ошибка установки мода: {}", exc)
                self.after(
                    0,
                    lambda err=str(exc): status_label.configure(
                        text=f"❌ Ошибка: {err}", text_color="red"
                    ),
                )

        threading.Thread(target=install, daemon=True).start()

    def destroy(self) -> None:
        """Закрывает клиент при уничтожении."""
        try:
            if hasattr(self, "client") and self.client._session:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.client.close())
                loop.close()
        except Exception:
            pass
        super().destroy()
