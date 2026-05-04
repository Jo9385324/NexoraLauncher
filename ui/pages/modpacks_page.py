"""Страница модпаков (поиск на Modrinth + импорт .mrpack)."""

import asyncio
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from loguru import logger
from PIL import Image, ImageTk

from quantumlauncher.api.modrinth import ModrinthClient
from quantumlauncher.core.pack_manager import import_mrpack


class ModpacksPage(ctk.CTkFrame):
    """Страница модпаков."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.client = ModrinthClient()
        self._modpack_images: dict[str, ImageTk.PhotoImage] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_tabs()
        self._load_popular_modpacks()

    def _load_popular_modpacks(self) -> None:
        """Загружает популярные модпаки при старте."""
        self.controller.set_status("Загрузка популярных модпаков...")

        def load() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                popular = loop.run_until_complete(self._fetch_popular())
                self.after(0, lambda: self._show_popular_results(popular))
            except Exception as exc:
                logger.error("Ошибка загрузки популярных модпаков: {}", exc)
            finally:
                loop.close()
                self.after(0, lambda: self.controller.set_status("Готов"))

        threading.Thread(target=load, daemon=True).start()

    async def _fetch_popular(self) -> list[dict]:
        """Получает популярные модпаки с Modrinth."""
        async with self.client:
            projects = await self.client.get_featured_projects(
                project_type="modpack",
                limit=12,
            )
        return [
            {
                "id": p.project_id,
                "title": p.title,
                "description": p.description,
                "downloads": p.downloads,
                "icon_url": p.icon_url or "",
                "categories": p.categories,
            }
            for p in projects
        ]

    def _show_popular_results(self, results: list[dict]) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.results_frame,
            text="🔥 Популярные модпаки",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#e74c3c", "#ff6b6b"),
        ).pack(pady=(10, 10), anchor="w", padx=2)

        for item in results:
            self._add_modpack_card(item)

        self.controller.set_status(f"Показано {len(results)} популярных модпаков")
        self._load_popular_modpacks()

    def _create_header(self) -> None:
        """Создаёт заголовок."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(
            header,
            text="📦  Модпаки",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(side="left")

    def _create_tabs(self) -> None:
        """Создаёт вкладки."""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.popular_tab = self.tabview.add("🔥 Популярное")
        self.search_tab = self.tabview.add("🔍 Поиск")
        self.import_tab = self.tabview.add("📁 Импорт")

        self._create_popular_tab()
        self._create_search_tab()
        self._create_import_tab()

    # ─────────────────────── Популярное ───────────────────────

    def _create_popular_tab(self) -> None:
        """Создаёт вкладку популярных модпаков."""
        self.popular_tab.grid_columnconfigure(0, weight=1)
        self.popular_tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.popular_tab, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="Популярные модпаки",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header,
            text="🔄 Обновить",
            width=100,
            command=self._load_popular_modpacks,
        )
        refresh_btn.pack(side="right", padx=10)

        self.popular_frame = ctk.CTkScrollableFrame(self.popular_tab)
        self.popular_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.popular_progress = ctk.CTkProgressBar(self.popular_tab, mode="indeterminate")
        self.popular_progress.grid(row=2, column=0, sticky="ew", pady=(5, 10))
        self.popular_progress.set(0)

    def _load_popular_modpacks(self) -> None:
        """Загружает популярные модпаки в фоне."""
        self.popular_progress.start()
        self.controller.set_status("Загрузка популярных модпаков...")

        def load() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self._fetch_popular_modpacks())
                self.after(0, lambda: self._show_popular_results(results))
            except Exception as exc:
                logger.error("Ошибка загрузки популярных модпаков: {}", exc)
                self.after(
                    0, lambda err=str(exc): self.controller.set_status(f"Ошибка: {err}")
                )
            finally:
                loop.close()
                self.after(0, self.popular_progress.stop)

        threading.Thread(target=load, daemon=True).start()

    async def _fetch_popular_modpacks(self) -> list[dict]:
        """Получает список популярных модпаков."""
        async with self.client:
            facets = [["project_type:modpack"]]
            projects = await self.client.search("", facets=facets, limit=20)
        return [
            {
                "id": p.project_id,
                "title": p.title,
                "description": p.description,
                "downloads": p.downloads,
                "icon_url": p.icon_url or "",
                "categories": p.categories,
            }
            for p in projects[:20]
        ]

    def _show_popular_results(self, results: list[dict]) -> None:
        """Отображает популярные модпаки."""
        for w in self.popular_frame.winfo_children():
            w.destroy()

        if not results:
            ctk.CTkLabel(
                self.popular_frame,
                text="Не удалось загрузить модпаки",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        for item in results:
            self._add_modpack_card(item)

        self.controller.set_status(f"Загружено {len(results)} модпаков")

    # ─────────────────────── Поиск ───────────────────────

    # ─────────────────────── Поиск ───────────────────────

    def _create_search_tab(self) -> None:
        """Создаёт вкладку поиска модпаков."""
        self.search_tab.grid_columnconfigure(0, weight=1)
        self.search_tab.grid_rowconfigure(2, weight=1)

        search_panel = ctk.CTkFrame(self.search_tab, fg_color="transparent")
        search_panel.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        search_panel.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_panel,
            placeholder_text="Поиск модпаков на Modrinth...",
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=10,
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda _e: self._on_search())

        self.search_btn = ctk.CTkButton(
            search_panel,
            text="🔍 Найти",
            width=110,
            height=40,
            command=self._on_search,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.search_btn.grid(row=0, column=1)

        self.progress = ctk.CTkProgressBar(self.search_tab, mode="indeterminate")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(5, 5))
        self.progress.set(0)

        self.results_frame = ctk.CTkScrollableFrame(self.search_tab)
        self.results_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        self._show_placeholder("Введите запрос для поиска модпаков")

    def _show_placeholder(self, text: str) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.results_frame,
            text=text,
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(pady=40)

    def _on_search(self) -> None:
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_btn.configure(state="disabled")
        self.progress.start()
        self.controller.set_status(f"Поиск модпаков '{query}'...")

        def search() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self._do_search(query))
                self.after(0, lambda: self._show_results(results))
            except Exception as exc:
                logger.error("Ошибка поиска модпаков: {}", exc)
                self.after(
                    0, lambda err=str(exc): self.controller.set_status(f"Ошибка: {err}")
                )
            finally:
                loop.close()
                self.after(0, self.progress.stop)
                self.after(0, lambda: self.search_btn.configure(state="normal"))

        threading.Thread(target=search, daemon=True).start()

    async def _do_search(self, query: str) -> list[dict]:
        async with self.client:
            # Фильтр по типу проекта: модпак
            facets = [["project_type:modpack"]]
            projects = await self.client.search(
                query, facets=facets, limit=20
            )
        return [
            {
                "id": p.project_id,
                "title": p.title,
                "description": p.description,
                "downloads": p.downloads,
                "icon_url": p.icon_url or "",
                "categories": p.categories,
            }
            for p in projects
        ]

    def _show_results(self, results: list[dict]) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()

        if not results:
            self._show_placeholder("Ничего не найдено")
            self.controller.set_status("Ничего не найдено")
            return

        for item in results:
            self._add_modpack_card(item)

        self.controller.set_status(f"Найдено {len(results)} модпаков")

    def _add_modpack_card(self, item: dict) -> None:
        card = ctk.CTkFrame(self.results_frame, corner_radius=10)
        card.pack(fill="x", pady=4, padx=2)

        # Иконка
        icon_url = item.get("icon_url", "")
        icon_label = ctk.CTkLabel(card, text="", width=48, height=48)
        icon_label.pack(side="left", padx=(10, 10), pady=8)

        if icon_url:
            threading.Thread(
                target=lambda: self._load_icon(icon_url, icon_label, item["id"]),
                daemon=True,
            ).start()
        else:
            icon_label.configure(text="📦")

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=0, pady=8)

        ctk.CTkLabel(
            info,
            text=item["title"],
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w")

        desc = item["description"]
        if desc and len(desc) > 120:
            desc = desc[:120] + "..."
        if desc:
            ctk.CTkLabel(
                info,
                text=desc,
                font=ctk.CTkFont(size=12),
                text_color="gray",
                wraplength=400,
            ).pack(anchor="w", pady=(4, 0))

        cats = " / ".join(item.get("categories", [])[:3])
        ctk.CTkLabel(
            info,
            text=f"⬇ {item['downloads']:,}  •  {cats}",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            card,
            text="⬇ Скачать .mrpack",
            width=140,
            height=32,
            command=lambda i=item: self._download_mrpack(i),
        ).pack(side="right", padx=10, pady=8)

    def _load_icon(self, icon_url: str, label: ctk.CTkLabel, pack_id: str) -> None:
        """Загружает иконку модпака."""
        try:
            import requests

            resp = requests.get(icon_url, timeout=5)
            if resp.status_code == 200:
                img = Image.open(resp.content)
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self._modpack_images[pack_id] = tk_img
                self.after(0, lambda: label.configure(image=tk_img))
        except Exception as exc:
            logger.debug("Не удалось загрузить иконку {}: {}", icon_url, exc)

    def _download_mrpack(self, item: dict) -> None:
        """Скачивает модпак и предлагает установить."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(item["title"])
        dialog.geometry("450x250")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f"Установка: {item['title']}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            dialog,
            text="Название нового инстанса:",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=20, pady=(10, 5))

        name_entry = ctk.CTkEntry(dialog, font=ctk.CTkFont(size=13))
        name_entry.pack(fill="x", padx=20, pady=(0, 10))
        name_entry.insert(0, item["title"].replace(" ", "_")[:30])

        status = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        status.pack(pady=5)

        def do_install() -> None:
            name = name_entry.get().strip()
            if not name:
                status.configure(text="Введите название", text_color="red")
                return
            self._install_mrpack_from_modrinth(item["id"], name, dialog, status)

        ctk.CTkButton(
            dialog,
            text="⬇ Скачать и установить",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=do_install,
        ).pack(pady=10)

    def _install_mrpack_from_modrinth(
        self, project_id: str, name: str, dialog: ctk.CTkToplevel, status: ctk.CTkLabel
    ) -> None:
        """Скачивает .mrpack с Modrinth и устанавливает."""
        from quantumlauncher.utils.paths import get_modpacks_dir

        status.configure(text="⏳ Скачивание модпака...", text_color="orange")
        dialog.update()

        def do_install() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def _download() -> Path:
                    async with self.client:
                        versions = await self.client.get_project_versions(project_id)
                        if not versions:
                            raise ValueError("Нет доступных версий")
                        ver = versions[0]
                        file_info = self.client.get_primary_file(ver)
                        if file_info is None:
                            raise ValueError("Нет файлов для скачивания")

                        dest = get_modpacks_dir() / file_info["filename"]
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        await self.client.download_file(file_info["url"], str(dest))
                        return dest

                mrpack_path = loop.run_until_complete(_download())
                loop.close()

                # Устанавливаем
                import_mrpack(mrpack_path, name)
                self.after(
                    0,
                    lambda: status.configure(
                        text=f"✅ Модпак '{name}' установлен", text_color="green"
                    ),
                )
                self.after(
                    0,
                    lambda: self.controller.set_status(f"Модпак '{name}' установлен"),
                )
            except Exception as exc:
                logger.error("Ошибка установки модпака: {}", exc)
                self.after(
                    0,
                    lambda err=str(exc): status.configure(
                        text=f"❌ Ошибка: {err}", text_color="red"
                    ),
                )

        threading.Thread(target=do_install, daemon=True).start()

    # ─────────────────────── Импорт ──────────────────────

    def _create_import_tab(self) -> None:
        """Создаёт вкладку импорта из файла."""
        frame = ctk.CTkFrame(self.import_tab, fg_color="transparent")
        frame.pack(expand=True, pady=40)

        ctk.CTkLabel(
            frame,
            text="📁 Импорт модпака из .mrpack",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            frame,
            text="Выберите файл .mrpack для установки",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack(pady=(0, 20))

        ctk.CTkButton(
            frame,
            text="Выбрать файл",
            width=160,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._import_from_file,
        ).pack(pady=10)

    def _import_from_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Modrinth Pack", "*.mrpack")],
            title="Выберите .mrpack файл",
        )
        if not path:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Импорт модпака")
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
                import_mrpack(Path(path), name)
                status.configure(
                    text=f"✅ Модпак '{name}' установлен", text_color="green"
                )
                self.controller.set_status(f"Модпак '{name}' импортирован")
                dialog.after(1000, dialog.destroy)
            except Exception as exc:
                logger.error("Ошибка импорта модпака: {}", exc)
                status.configure(text=f"❌ Ошибка: {exc}", text_color="red")

        ctk.CTkButton(
            dialog,
            text="Импортировать",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=do_import,
        ).pack(pady=10)

    def destroy(self) -> None:
        try:
            if self.client._session:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.client.close())
                loop.close()
        except Exception:
            pass
        self._image_cache.clear()
        super().destroy()
