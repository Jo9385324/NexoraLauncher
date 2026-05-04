"""Страница карт (поиск на Modrinth + установка в saves)."""

import asyncio
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from loguru import logger
from PIL import Image, ImageTk

from quantumlauncher.api.modrinth import ModrinthClient
from quantumlauncher.core.instance import Instance, InstanceManager


class MapsPage(ctk.CTkFrame):
    """Страница карт Minecraft."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.client = ModrinthClient()
        self._map_images: dict[str, ImageTk.PhotoImage] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_tabs()
        self._load_popular_maps()

    def _load_popular_maps(self) -> None:
        """Загружает популярные карты при старте."""
        self.controller.set_status("Загрузка популярных карт...")

        def load() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                popular = loop.run_until_complete(self._fetch_popular())
                self.after(0, lambda: self._show_popular_results(popular))
            except Exception as exc:
                logger.error("Ошибка загрузки популярных карт: {}", exc)
            finally:
                loop.close()
                self.after(0, lambda: self.controller.set_status("Готов"))

        threading.Thread(target=load, daemon=True).start()

    async def _fetch_popular(self) -> list[dict]:
        """Получает популярные карты с Modrinth."""
        async with self.client:
            projects = await self.client.get_featured_projects(
                project_type="map",
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
            text="🗺️ Популярные карты",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#3498db", "#5dade2"),
        ).pack(pady=(10, 10), anchor="w", padx=2)

        for item in results:
            self._add_map_card(item)

        self.controller.set_status(f"Показано {len(results)} популярных карт")
        self._load_popular_maps()

    def _create_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(
            header,
            text="🗺️  Карты",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(side="left")

    def _create_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew")

        self.popular_tab = self.tabview.add("🔥 Популярное")
        self.search_tab = self.tabview.add("🔍 Поиск")
        self.installed_tab = self.tabview.add("✅ Установленные")

        self._create_popular_tab()
        self._create_search_tab()
        self._create_installed_tab()

    # ─────────────────────── Популярное ───────────────────────

    def _create_popular_tab(self) -> None:
        """Создаёт вкладку популярных карт."""
        self.popular_tab.grid_columnconfigure(0, weight=1)
        self.popular_tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.popular_tab, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="Популярные карты",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header,
            text="🔄 Обновить",
            width=100,
            command=self._load_popular_maps,
        )
        refresh_btn.pack(side="right", padx=10)

        self.popular_frame = ctk.CTkScrollableFrame(self.popular_tab)
        self.popular_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.popular_progress = ctk.CTkProgressBar(self.popular_tab, mode="indeterminate")
        self.popular_progress.grid(row=2, column=0, sticky="ew", pady=(5, 10))
        self.popular_progress.set(0)

    def _load_popular_maps(self) -> None:
        """Загружает популярные карты в фоне."""
        self.popular_progress.start()
        self.controller.set_status("Загрузка популярных карт...")

        def load() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self._fetch_popular_maps())
                self.after(0, lambda: self._show_popular_results(results))
            except Exception as exc:
                logger.error("Ошибка загрузки популярных карт: {}", exc)
                self.after(
                    0, lambda err=str(exc): self.controller.set_status(f"Ошибка: {err}")
                )
            finally:
                loop.close()
                self.after(0, self.popular_progress.stop)

        threading.Thread(target=load, daemon=True).start()

    async def _fetch_popular_maps(self) -> list[dict]:
        """Получает список популярных карт."""
        async with self.client:
            facets = [["project_type:map"]]
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
        """Отображает популярные карты."""
        for w in self.popular_frame.winfo_children():
            w.destroy()

        if not results:
            ctk.CTkLabel(
                self.popular_frame,
                text="Не удалось загрузить карты",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        for item in results:
            self._add_map_card(item)

        self.controller.set_status(f"Загружено {len(results)} карт")

    # ─────────────────────── Поиск ───────────────────────

    # ─────────────────────── Поиск ───────────────────────

    def _create_search_tab(self) -> None:
        self.search_tab.grid_columnconfigure(0, weight=1)
        self.search_tab.grid_rowconfigure(2, weight=1)

        search_panel = ctk.CTkFrame(self.search_tab, fg_color="transparent")
        search_panel.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        search_panel.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_panel,
            placeholder_text="Поиск карт на Modrinth...",
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

        self._show_placeholder("Введите запрос для поиска карт")

    def _show_placeholder(self, text: str) -> None:
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.results_frame, text=text, font=ctk.CTkFont(size=14), text_color="gray"
        ).pack(pady=40)

    def _on_search(self) -> None:
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_btn.configure(state="disabled")
        self.progress.start()
        self.controller.set_status(f"Поиск карт '{query}'...")

        def search() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self._do_search(query))
                self.after(0, lambda: self._show_results(results))
            except Exception as exc:
                logger.error("Ошибка поиска карт: {}", exc)
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
            facets = [["project_type:map"]]
            projects = await self.client.search(query, facets=facets, limit=20)
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
            self._add_map_card(item)

        self.controller.set_status(f"Найдено {len(results)} карт")

    def _add_map_card(self, item: dict) -> None:
        card = ctk.CTkFrame(self.results_frame, corner_radius=10)
        card.pack(fill="x", pady=4, padx=2)

        icon_url = item.get("icon_url", "")
        icon_label = ctk.CTkLabel(card, text="", width=48, height=48)
        icon_label.pack(side="left", padx=(10, 10), pady=8)

        if icon_url:
            threading.Thread(
                target=lambda: self._load_icon(icon_url, icon_label, item["id"]),
                daemon=True,
            ).start()
        else:
            icon_label.configure(text="🗺️")

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
            text="⬇ Установить",
            width=110,
            height=32,
            command=lambda i=item: self._show_install_dialog(i),
        ).pack(side="right", padx=10, pady=8)

    def _load_icon(self, icon_url: str, label: ctk.CTkLabel, map_id: str) -> None:
        """Загружает иконку карты."""
        try:
            import requests

            resp = requests.get(icon_url, timeout=5)
            if resp.status_code == 200:
                img = Image.open(resp.content)
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self._map_images[map_id] = tk_img
                self.after(0, lambda: label.configure(image=tk_img))
        except Exception as exc:
            logger.debug("Не удалось загрузить иконку {}: {}", icon_url, exc)

    def _show_install_dialog(self, item: dict) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title(item["title"])
        dialog.geometry("450x300")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=item["title"],
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            dialog,
            text="Выберите инстанс для установки карты:",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=5)

        instances = InstanceManager.list_instances()
        names = [i.name for i in instances] if instances else ["Нет инстансов"]
        inst_var = ctk.StringVar(value=names[0])
        ctk.CTkComboBox(
            dialog, values=names, variable=inst_var, font=ctk.CTkFont(size=12)
        ).pack(fill="x", padx=20, pady=10)

        status = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        status.pack(pady=5)

        def on_install() -> None:
            iname = inst_var.get()
            if iname == "Нет инстансов":
                status.configure(text="❌ Создайте инстанс", text_color="red")
                return
            self._install_map(item, iname, dialog, status)

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(pady=10)
        ctk.CTkButton(btns, text="Закрыть", command=dialog.destroy).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            btns,
            text="⬇ Установить",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=on_install,
        ).pack(side="left", padx=5)

    def _install_map(
        self,
        item: dict,
        instance_name: str,
        dialog: ctk.CTkToplevel,
        status: ctk.CTkLabel,
    ) -> None:
        instance = Instance.load(instance_name)
        if instance is None:
            status.configure(text="❌ Инстанс не найден", text_color="red")
            return

        status.configure(text="⏳ Скачивание карты...", text_color="orange")
        dialog.update()

        def do_install() -> None:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def _download() -> str:
                    async with self.client:
                        versions = await self.client.get_project_versions(item["id"])
                        if not versions:
                            raise ValueError("Нет доступных версий")
                        ver = versions[0]
                        file_info = self.client.get_primary_file(ver)
                        if file_info is None:
                            raise ValueError("Нет файлов")

                        saves_dir = instance.game_dir / "saves"
                        saves_dir.mkdir(parents=True, exist_ok=True)
                        dest = saves_dir / file_info["filename"]
                        await self.client.download_file(file_info["url"], str(dest))
                        return str(dest)

                result = loop.run_until_complete(_download())
                loop.close()

                # Если .zip — распаковываем
                if result.endswith(".zip"):
                    import zipfile

                    extract_to = instance.game_dir / "saves"
                    with zipfile.ZipFile(result, "r") as zf:
                        zf.extractall(extract_to)
                    Path(result).unlink()

                self.after(
                    0,
                    lambda: status.configure(
                        text="✅ Карта установлена", text_color="green"
                    ),
                )
                self.after(
                    0,
                    lambda: self.controller.set_status(
                        f"Карта {item['title']} установлена в {instance_name}"
                    ),
                )
            except Exception as exc:
                logger.error("Ошибка установки карты: {}", exc)
                self.after(
                    0,
                    lambda err=str(exc): status.configure(
                        text=f"❌ Ошибка: {err}", text_color="red"
                    ),
                )

        threading.Thread(target=do_install, daemon=True).start()

    # ─────────────────── Установленные ───────────────────

    def _create_installed_tab(self) -> None:
        self.installed_tab.grid_columnconfigure(0, weight=1)
        self.installed_tab.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self.installed_tab, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(10, 5))

        ctk.CTkLabel(top, text="Инстанс:", font=ctk.CTkFont(size=12)).pack(side="left")
        self.instance_var = ctk.StringVar()
        self.instance_combo = ctk.CTkComboBox(
            top,
            variable=self.instance_var,
            values=self._get_instance_names(),
            width=200,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._load_installed_maps(),
        )
        self.instance_combo.pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            top,
            text="🔄 Обновить",
            width=100,
            command=self._load_installed_maps,
        ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            top,
            text="📁 Добавить",
            width=130,
            command=self._add_map_from_file,
        ).pack(side="right")

        self.installed_list = ctk.CTkScrollableFrame(self.installed_tab)
        self.installed_list.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

    def _get_instance_names(self) -> list[str]:
        instances = InstanceManager.list_instances()
        return [i.name for i in instances] if instances else ["Нет инстансов"]

    def _load_installed_maps(self) -> None:
        for w in self.installed_list.winfo_children():
            w.destroy()

        name = self.instance_var.get()
        if not name or name == "Нет инстансов":
            ctk.CTkLabel(
                self.installed_list,
                text="Выберите инстанс",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=30)
            return

        instance = Instance.load(name)
        if instance is None:
            return

        saves_dir = instance.game_dir / "saves"
        if not saves_dir.exists():
            ctk.CTkLabel(
                self.installed_list,
                text="Нет установленных карт",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=30)
            return

        # Ищем папки карт (не .zip, не datapacks)
        maps = sorted(
            [d for d in saves_dir.iterdir() if d.is_dir() and (d / "level.dat").exists()],
            key=lambda p: p.name.lower(),
        )
        if not maps:
            ctk.CTkLabel(
                self.installed_list,
                text="Нет установленных карт",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=30)
            return

        for m in maps:
            self._add_map_row(m, instance)

        ctk.CTkLabel(
            self.installed_list,
            text=f"Всего карт: {len(maps)}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(pady=(10, 0))

    def _add_map_row(self, map_dir: Path, instance: Instance) -> None:
        row = ctk.CTkFrame(self.installed_list, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(
            row,
            text=map_dir.name,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            row,
            text="🗑",
            width=36,
            height=28,
            fg_color="transparent",
            hover_color=("#aa3333", "#aa3333"),
            text_color=("#cc4444", "#ff6666"),
            command=lambda m=map_dir, i=instance: self._delete_map(m, i),
        ).pack(side="right", padx=5)

    def _add_map_from_file(self) -> None:
        name = self.instance_var.get()
        if not name or name == "Нет инстансов":
            self.controller.set_status("❌ Выберите инстанс")
            return

        instance = Instance.load(name)
        if instance is None:
            return

        paths = filedialog.askopenfilenames(
            filetypes=[("ZIP архивы", "*.zip"), ("Все файлы", "*.*")],
            title="Выберите карты",
        )
        if not paths:
            return

        import shutil
        import zipfile

        copied = 0
        for src in paths:
            try:
                saves_dir = instance.game_dir / "saves"
                saves_dir.mkdir(parents=True, exist_ok=True)
                if src.endswith(".zip"):
                    with zipfile.ZipFile(src, "r") as zf:
                        zf.extractall(saves_dir)
                else:
                    dest = saves_dir / Path(src).name
                    shutil.copy2(src, dest)
                copied += 1
            except Exception as exc:
                logger.error("Ошибка копирования карты {}: {}", src, exc)

        self._load_installed_maps()
        self.controller.set_status(f"✅ Добавлено {copied} карт в {name}")

    def _delete_map(self, map_dir: Path, instance: Instance) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Удалить карту")
        dialog.geometry("350x130")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f'Удалить "{map_dir.name}"?',
            font=ctk.CTkFont(size=13),
        ).pack(pady=15)

        def confirm() -> None:
            try:
                import shutil

                shutil.rmtree(map_dir)
                dialog.destroy()
                self._load_installed_maps()
                self.controller.set_status(f"🗑 {map_dir.name} удалена")
            except Exception as exc:
                logger.error("Ошибка удаления карты: {}", exc)

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(pady=5)
        ctk.CTkButton(btns, text="Отмена", command=dialog.destroy).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            btns,
            text="Удалить",
            fg_color="#cc4444",
            hover_color="#aa2222",
            command=confirm,
        ).pack(side="left", padx=5)

    def destroy(self) -> None:
        try:
            if self.client._session:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.client.close())
                loop.close()
        except Exception:
            pass
        super().destroy()
