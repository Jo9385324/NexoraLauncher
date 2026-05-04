"""Страница управления шейдерами."""

import threading
from pathlib import Path

import customtkinter as ctk
import requests
from loguru import logger
from PIL import Image, ImageTk

from quantumlauncher.core.instance import Instance, InstanceManager


class ShadersPage(ctk.CTkFrame):
    """Страница шейдеров — поиск и управление per-instance."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self._shader_images: dict[str, ImageTk.PhotoImage] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_instance_selector()
        self._create_tabs()

    def _create_tabs(self) -> None:
        """Создаёт вкладки для шейдеров."""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        self.popular_tab = self.tabview.add("🔥 Популярное")
        self.search_tab = self.tabview.add("🔍 Поиск")
        self.installed_tab = self.tabview.add("✅ Установленные")

        self._create_popular_tab()
        self._create_search_tab()
        self._create_installed_tab()

    # ─────────────────────── Популярное ───────────────────────

    def _create_popular_tab(self) -> None:
        """Создаёт вкладку популярных шейдеров."""
        self.popular_tab.grid_columnconfigure(0, weight=1)
        self.popular_tab.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.popular_tab, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(10, 5))

        ctk.CTkLabel(
            header,
            text="Популярные шейдеры",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header,
            text="🔄 Обновить",
            width=100,
            command=self._load_popular_shaders,
        )
        refresh_btn.pack(side="right", padx=10)

        self.popular_frame = ctk.CTkScrollableFrame(self.popular_tab)
        self.popular_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.popular_progress = ctk.CTkProgressBar(self.popular_tab, mode="indeterminate")
        self.popular_progress.grid(row=2, column=0, sticky="ew", pady=(5, 10))
        self.popular_progress.set(0)

        # Загружаем популярные шейдеры при создании вкладки
        self._load_popular_shaders()

    def _load_popular_shaders(self) -> None:
        """Загружает популярные шейдеры в фоне."""
        self.popular_progress.start()
        self.controller.set_status("Загрузка популярных шейдеров...")

        def load() -> None:
            try:
                popular = self._fetch_popular_sync()
                self.after(0, lambda: self._show_popular_results(popular))
            except Exception as exc:
                logger.error("Ошибка загрузки популярных шейдеров: {}", exc)
                self.after(
                    0, lambda err=str(exc): self.controller.set_status(f"Ошибка: {err}")
                )
            finally:
                self.after(0, self.popular_progress.stop)

        threading.Thread(target=load, daemon=True).start()

    def _fetch_popular_sync(self) -> list[dict]:
        """Получает популярные шейдеры с Modrinth (синхронно)."""
        import requests

        url = "https://api.modrinth.com/v2/search"
        params = {
            "limit": 12,
            "index": "featured",
            "facets": '[["project_type:shaderpack"]]',
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        hits = data.get("hits", [])
        return [
            {
                "id": h.get("slug", ""),
                "title": h.get("title", "Unknown"),
                "description": h.get("description", "") or "",
                "downloads": h.get("downloads", 0),
                "icon_url": h.get("icon_url", "") or "",
                "categories": h.get("categories", []),
            }
            for h in hits[:12]
        ]

    def _show_popular_results(self, results: list[dict]) -> None:
        """Показывает популярные шейдеры."""
        for w in self.popular_frame.winfo_children():
            w.destroy()

        if not results:
            ctk.CTkLabel(
                self.popular_frame,
                text="Не удалось загрузить шейдеры",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        for item in results:
            self._add_shader_card_popular(item)

        self.controller.set_status(f"Показано {len(results)} популярных шейдеров")

    # ─────────────────────── Поиск ───────────────────────

    def _add_shader_card_popular(self, item: dict) -> None:
        """Добавляет карточку популярного шейдера."""
        card = ctk.CTkFrame(self.popular_frame, corner_radius=10)
        card.pack(fill="x", pady=4, padx=2)

        icon_url = item.get("icon_url", "")
        icon_label = ctk.CTkLabel(card, text="🌈", width=48, height=48)
        icon_label.pack(side="left", padx=(10, 10), pady=8)

        if icon_url and icon_url.startswith("http"):
            threading.Thread(
                target=lambda: self._load_icon(icon_url, icon_label, item["id"]),
                daemon=True,
            ).start()

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=0, pady=8)

        ctk.CTkLabel(
            info,
            text=item["title"],
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w")

        desc = item.get("description", "")
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
        downloads = item.get("downloads", 0)
        ctk.CTkLabel(
            info,
            text=f"⬇ {downloads:,}  •  {cats}" if cats else f"⬇ {downloads:,}",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            card,
            text="⬇ Скачать",
            width=100,
            height=32,
            command=lambda i=item: self._download_shader_popular(i),
        ).pack(side="right", padx=10, pady=8)

    def _load_icon(self, icon_url: str, label: ctk.CTkLabel, shader_id: str) -> None:
        """Загружает иконку шейдера."""
        try:
            import requests

            resp = requests.get(icon_url, timeout=5, stream=True)
            if resp.status_code == 200:
                img = Image.open(resp.raw)
                img = img.convert("RGBA")
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self._shader_images[shader_id] = tk_img
                self.after(0, lambda lbl=label, i=tk_img: lbl.configure(image=i))
        except Exception as exc:
            logger.debug("Не удалось загрузить иконку {}: {}", icon_url, exc)
            self.after(0, lambda lbl=label: lbl.configure(text="🌈"))

    def _download_shader_popular(self, item: dict) -> None:
        """Скачивает популярный шейдер."""
        shaders_dir = self._get_shaders_dir()
        if shaders_dir is None:
            self.controller.set_status("❌ Выберите инстанс")
            return

        self.controller.set_status(f"⬇ Скачивание {item['title']}...")

        def download() -> None:
            try:
                url = f"https://api.modrinth.com/v2/project/{item['id']}/version"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                versions = response.json()
                if not versions:
                    raise ValueError("Нет версий")

                for v in versions:
                    files = v.get("files", [])
                    for f in files:
                        if f.get("primary", False) and f.get("url"):
                            self._save_shader(f["url"], f["filename"], shaders_dir)
                            self.after(
                                0, lambda: self.controller.set_status(f"✅ {item['title']} скачан")
                            )
                            self.after(0, self._load_installed_shaders)
                            return

                raise ValueError("Нет файлов для скачивания")
            except Exception as exc:
                logger.error("Ошибка скачивания шейдера: {}", exc)
                msg = str(exc)
                self.after(0, lambda m=msg: self.controller.set_status(f"❌ Ошибка: {m}"))

        threading.Thread(target=download, daemon=True).start()

    # ─────────────────────── Поиск ───────────────────────

    def _create_search_tab(self) -> None:
        """Создаёт вкладку поиска шейдеров."""
        self.search_tab.grid_columnconfigure(0, weight=1)
        self.search_tab.grid_rowconfigure(2, weight=1)

        search_panel = ctk.CTkFrame(self.search_tab, fg_color="transparent")
        search_panel.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        search_panel.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_panel,
            placeholder_text="Поиск шейдеров (BSL, Sildurs, Complementary...)",
            font=ctk.CTkFont(size=14),
            height=38,
            corner_radius=10,
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.search_entry.bind("<Return>", lambda _e: self._search_shaders())

        self.search_btn = ctk.CTkButton(
            search_panel,
            text="🔍 Поиск",
            width=110,
            height=38,
            command=self._search_shaders,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.search_btn.grid(row=0, column=1)

        self.progress = ctk.CTkProgressBar(self.search_tab, mode="indeterminate")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(5, 5))
        self.progress.set(0)

        self.search_results_frame = ctk.CTkScrollableFrame(self.search_tab)
        self.search_results_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        self._show_search_placeholder("Введите запрос для поиска шейдеров")

    def _show_search_placeholder(self, text: str) -> None:
        """Показывает placeholder в результатах поиска."""
        for w in self.search_results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.search_results_frame,
            text=text,
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(pady=40)

    def _search_shaders(self) -> None:
        """Ищет шейдеры на Modrinth."""
        query = self.search_entry.get().strip()
        if not query:
            self.controller.set_status("Введите название шейдеров")
            return

        self.controller.set_status("🔍 Поиск шейдеров...")
        self.search_btn.configure(state="disabled")
        self.progress.start()

        def search() -> None:
            try:
                import requests

                url = "https://api.modrinth.com/v2/search"
                params = {
                    "query": query,
                    "index": "downloads",
                    "facets": '[["project_type:shaderpack"]]',
                    "limit": 10,
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                results = data.get("hits", [])
                self.after(0, lambda r=results: self._show_search_results(r))
            except Exception as exc:
                logger.error("Ошибка поиска шейдеров: {}", exc)
                msg = str(exc)
                self.after(0, lambda m=msg: self.controller.set_status(f"❌ Ошибка: {m}"))
            finally:
                self.after(0, self.progress.stop)
                self.after(0, lambda: self.search_btn.configure(state="normal"))

        threading.Thread(target=search, daemon=True).start()

    def _show_search_results(self, results: list) -> None:
        """Показывает результаты поиска."""
        for w in self.search_results_frame.winfo_children():
            w.destroy()

        if not results:
            self._show_search_placeholder("Ничего не найдено")
            self.controller.set_status("Ничего не найдено")
            return

        for item in results:
            self._add_shader_search_card(item)

        self.controller.set_status(f"Найдено {len(results)} шейдеров")

    def _add_shader_search_card(self, item: dict) -> None:
        """Добавляет карточку шейдера из результатов поиска."""
        card = ctk.CTkFrame(self.search_results_frame, corner_radius=10)
        card.pack(fill="x", pady=4, padx=2)

        icon_url = item.get("icon_url", "")
        icon_label = ctk.CTkLabel(card, text="🌈", width=48, height=48)
        icon_label.pack(side="left", padx=(10, 10), pady=8)

        if icon_url and icon_url.startswith("http"):
            threading.Thread(
                target=lambda: self._load_icon(icon_url, icon_label, item["id"]),
                daemon=True,
            ).start()

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=0, pady=8)

        ctk.CTkLabel(
            info,
            text=item["title"],
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w")

        desc = item.get("description", "")
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
        downloads = item.get("downloads", 0)
        ctk.CTkLabel(
            info,
            text=f"⬇ {downloads:,}  •  {cats}" if cats else f"⬇ {downloads:,}",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(
            card,
            text="⬇ Скачать",
            width=100,
            height=32,
            command=lambda i=item: self._download_shader_from_search(i),
        ).pack(side="right", padx=10, pady=8)

    def _download_shader_from_search(self, item: dict) -> None:
        """Скачивает шейдер из результатов поиска."""
        shaders_dir = self._get_shaders_dir()
        if shaders_dir is None:
            self.controller.set_status("❌ Выберите инстанс")
            return

        self.controller.set_status(f"⬇ Скачивание {item['title']}...")

        def download() -> None:
            try:
                url = f"https://api.modrinth.com/v2/project/{item['id']}/version"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                versions = response.json()
                if not versions:
                    raise ValueError("Нет версий")

                for v in versions:
                    files = v.get("files", [])
                    for f in files:
                        if f.get("primary", False) and f.get("url"):
                            self._save_shader(f["url"], f["filename"], shaders_dir)
                            self.after(
                                0, lambda: self.controller.set_status(f"✅ {item['title']} скачан")
                            )
                            self.after(0, self._load_installed_shaders)
                            return

                raise ValueError("Нет файлов для скачивания")
            except Exception as exc:
                logger.error("Ошибка скачивания шейдера: {}", exc)
                msg = str(exc)
                self.after(0, lambda m=msg: self.controller.set_status(f"❌ Ошибка: {m}"))

        threading.Thread(target=download, daemon=True).start()

    # ─────────────────── Установленные ───────────────────

    def _create_installed_tab(self) -> None:
        """Создаёт вкладку установленных шейдеров."""
        self.installed_tab.grid_columnconfigure(0, weight=1)
        self.installed_tab.grid_rowconfigure(1, weight=1)

        self.installed_list = ctk.CTkScrollableFrame(self.installed_tab)
        self.installed_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Загружаем установленные шейдеры при создании вкладки
        self._load_installed_shaders()

    def _load_installed_shaders(self) -> None:
        """Загружает и отображает установленные шейдеры."""
        for widget in self.installed_list.winfo_children():
            widget.destroy()

        shaders_dir = self._get_shaders_dir()
        if shaders_dir is None:
            ctk.CTkLabel(
                self.installed_list,
                text="Выберите инстанс",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        shaders = list(shaders_dir.glob("*.zip"))
        if not shaders:
            ctk.CTkLabel(
                self.installed_list,
                text="Нет установленных шейдеров",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        for shader in shaders:
            self._add_shader_card(shader)

        ctk.CTkLabel(
            self.installed_list,
            text=f"Всего шейдеров: {len(shaders)}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(pady=(10, 0))

    def _add_shader_card(self, shader_path: Path) -> None:
        """Добавляет карточку установленного шейдера."""
        card = ctk.CTkFrame(self.installed_list, corner_radius=10)
        card.pack(fill="x", pady=4, padx=2)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        name_lbl = ctk.CTkLabel(
            info,
            text=shader_path.stem,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        name_lbl.pack(anchor="w")

        size_mb = shader_path.stat().st_size / (1024 * 1024)
        meta_lbl = ctk.CTkLabel(
            info,
            text=f"Размер: {size_mb:.1f} МБ",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        )
        meta_lbl.pack(anchor="w")

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(side="right", padx=12, pady=10)

        del_btn = ctk.CTkButton(
            btns,
            text="🗑",
            width=40,
            height=30,
            fg_color="transparent",
            hover_color=("#aa3333", "#aa3333"),
            text_color=("#cc4444", "#ff6666"),
            command=lambda p=shader_path: self._delete_shader(p),
        )
        del_btn.pack(side="left", padx=2)

    def _create_header(self) -> None:
        """Создаёт заголовок."""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        self.title_label = ctk.CTkLabel(
            self.header,
            text="🌈  Шейдеры",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.title_label.pack(side="left")

    def _create_instance_selector(self) -> None:
        """Создаёт выбор инстанса."""
        selector = ctk.CTkFrame(self, fg_color="transparent")
        selector.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(selector, text="Инстанс:", font=ctk.CTkFont(size=12)).pack(
            side="left"
        )
        self.instance_var = ctk.StringVar()
        self.instance_combo = ctk.CTkComboBox(
            selector,
            variable=self.instance_var,
            values=self._get_instance_names(),
            width=200,
            font=ctk.CTkFont(size=12),
            command=lambda _: self._load_installed_shaders(),
        )
        self.instance_combo.pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            selector,
            text="🔄 Обновить",
            width=100,
            command=self._load_installed_shaders,
        ).pack(side="left", padx=(10, 0))

    def _get_instance_names(self) -> list[str]:
        instances = InstanceManager.list_instances()
        return [i.name for i in instances] if instances else ["Нет инстансов"]

    def _get_shaders_dir(self) -> Path | None:
        """Возвращает путь к shaderpacks выбранного инстанса."""
        name = self.instance_var.get()
        if not name or name == "Нет инстансов":
            return None
        instance = Instance.load(name)
        if instance is None:
            return None
        shaders_dir = instance.game_dir / "shaderpacks"
        shaders_dir.mkdir(parents=True, exist_ok=True)
        return shaders_dir

    def _save_shader(self, url: str, filename: str, dest_dir: Path) -> None:
        """Сохраняет файл шейдера."""
        dest = dest_dir / filename
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with dest.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("Шейдер сохранён: {}", dest)

    def _delete_shader(self, shader_path: Path) -> None:
        """Удаляет шейдер."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Подтверждение")
        dialog.geometry("350x130")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f'Удалить шейдер "{shader_path.stem}"?',
            font=ctk.CTkFont(size=13),
        ).pack(pady=15)

        def confirm() -> None:
            try:
                shader_path.unlink()
                dialog.destroy()
                self._load_installed_shaders()
                self.controller.set_status(f"🗑 Шейдер '{shader_path.stem}' удалён")
            except Exception as exc:
                logger.error("Ошибка удаления шейдера: {}", exc)

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.pack(pady=10)

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
