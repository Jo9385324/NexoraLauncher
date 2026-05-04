"""Страница поиска и управления модами через Modrinth и CurseForge."""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from loguru import logger
from PIL import Image, ImageTk

from quantumlauncher.api.curseforge import CurseForgeClient
from quantumlauncher.api.modrinth import ModrinthClient
from quantumlauncher.core.instance import Instance, InstanceManager


class ModsPage(ctk.CTkFrame):
    """Страница модов с интеграцией Modrinth и CurseForge."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.modrinth = ModrinthClient()
        self.curseforge: CurseForgeClient | None = None
        self._current_source = "modrinth"
        self._search_results: list[dict] = []
        self._popular_mods: list[dict] = []
        self._mod_images: dict[str, ImageTk.PhotoImage] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_tabs()
        self._load_popular_mods()

    def _create_header(self) -> None:
        """Создаёт заголовок."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(
            header,
            text="🧩  Моды",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(side="left")

    def _create_tabs(self) -> None:
        """Создаёт вкладки."""
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
        """Создаёт вкладку популярных модов."""
        self.popular_tab.grid_columnconfigure(0, weight=1)
        self.popular_tab.grid_rowconfigure(0, weight=1)

        self.results_frame = ctk.CTkScrollableFrame(self.popular_tab)
        self.results_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def _load_popular_mods(self) -> None:
        """Загружает популярные моды при старте."""
        self.controller.set_status("Загрузка популярных модов...")

        def load() -> None:
            try:
                popular = self._fetch_popular_sync()
                root = self.winfo_toplevel()
                root.after(0, lambda: self._show_popular_results(popular))
            except Exception as exc:
                logger.error("Ошибка загрузки популярных модов: {}", exc)
                root = self.winfo_toplevel()
                root.after(0, lambda: self.controller.set_status("Готов"))
            finally:
                root = self.winfo_toplevel()
                root.after(0, lambda: self.controller.set_status("Готов"))

        threading.Thread(target=load, daemon=True).start()

    def _fetch_popular_sync(self) -> list[dict]:
        """Получает популярные моды с Modrinth (синхронно)."""
        import requests

        url = "https://api.modrinth.com/v2/search"
        params = {
            "limit": 12,
            "index": "featured",
            "facets": '[["project_type:mod"]]',
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
                "source": "modrinth",
                "icon_url": h.get("icon_url", "") or "",
                "categories": h.get("categories", []),
            }
            for h in hits
        ]

    def _show_popular_results(self, results: list[dict]) -> None:
        """Отображает популярные моды."""
        self._popular_mods = results
        for w in self.results_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.results_frame,
            text="🔥 Популярные моды",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#e74c3c", "#ff6b6b"),
        ).pack(pady=(10, 10), anchor="w", padx=2)

        for item in results:
            self._add_search_card(item)

        self.controller.set_status(f"Показано {len(results)} популярных модов")

    # ─────────────────────── Поиск ───────────────────────

    def _create_search_tab(self) -> None:
        """Создаёт содержимое вкладки поиска."""
        self.search_tab.grid_columnconfigure(0, weight=1)
        self.search_tab.grid_rowconfigure(2, weight=1)

        search_panel = ctk.CTkFrame(self.search_tab, fg_color="transparent")
        search_panel.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        search_panel.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_panel,
            placeholder_text="Поиск модов...",
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

        filters = ctk.CTkFrame(self.search_tab, fg_color="transparent")
        filters.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(filters, text="Источник:", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 5)
        )
        self.source_combo = ctk.CTkComboBox(
            filters,
            values=["Modrinth", "CurseForge"],
            width=130,
            font=ctk.CTkFont(size=12),
            command=self._on_source_change,
        )
        self.source_combo.set("Modrinth")
        self.source_combo.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(filters, text="Версия:", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 5)
        )
        self.version_filter = ctk.CTkEntry(
            filters,
            placeholder_text="1.20.1",
            width=100,
            font=ctk.CTkFont(size=12),
        )
        self.version_filter.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(filters, text="Загрузчик:", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(0, 5)
        )
        self.loader_filter = ctk.CTkComboBox(
            filters,
            values=["Любой", "fabric", "forge", "quilt", "neoforge"],
            width=120,
            font=ctk.CTkFont(size=12),
        )
        self.loader_filter.set("Любой")
        self.loader_filter.pack(side="left")

        self.results_frame = ctk.CTkScrollableFrame(self.search_tab)
        self.results_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        self._show_placeholder("Введите запрос для поиска модов")

        self.progress = ctk.CTkProgressBar(self.search_tab, mode="indeterminate")
        self.progress.grid(row=3, column=0, sticky="ew", pady=(5, 10))
        self.progress.set(0)

    def _on_source_change(self, value: str) -> None:
        """Обработчик смены источника."""
        self._current_source = value.lower().replace(" ", "")

    def _show_placeholder(self, text: str) -> None:
        """Показывает placeholder в списке результатов."""
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.results_frame,
            text=text,
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(pady=40)

    def _on_search(self) -> None:
        """Обработчик поиска."""
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_btn.configure(state="disabled")
        self.progress.start()
        self.controller.set_status(f"Поиск '{query}'...")

        def search() -> None:
            try:
                results = self._do_search_sync(query)
                root = self.winfo_toplevel()
                root.after(0, lambda: self._show_search_results(results))
            except Exception as exc:
                logger.error("Ошибка поиска модов: {}", exc)
                root = self.winfo_toplevel()
                root.after(0, lambda err=str(exc): self.controller.set_status(f"Ошибка: {err}"))
            finally:
                root = self.winfo_toplevel()
                root.after(0, self.progress.stop)
                root.after(0, lambda: self.search_btn.configure(state="normal"))

        threading.Thread(target=search, daemon=True).start()

    def _do_search_sync(self, query: str) -> list[dict]:
        """Выполняет синхронный поиск через requests."""
        import requests

        loader = self.loader_filter.get()

        if self._current_source == "curseforge":
            api_key = getattr(self.controller.config, "curseforge_api_key", "")
            if not api_key:
                return []
            # Для CurseForge нужно использовать async, пока вернём пустой список
            logger.warning("CurseForge поиск требует асинхронной реализации")
            return []

        facets: list[list[str]] = []
        if loader != "Любой":
            facets.append([f"categories:{loader}"])

        url = "https://api.modrinth.com/v2/search"
        params = {
            "query": query,
            "limit": 20,
            "facets": str(facets).replace("'", '"') if facets else None,
        }
        # Убираем None значения
        params = {k: v for k, v in params.items() if v is not None}

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
                "source": "modrinth",
                "icon_url": h.get("icon_url", "") or "",
                "categories": h.get("categories", []),
            }
            for h in hits
        ]

    def _show_search_results(self, results: list[dict]) -> None:
        """Отображает результаты поиска."""
        for w in self.results_frame.winfo_children():
            w.destroy()

        if not results:
            self._show_placeholder("Ничего не найдено")
            self.controller.set_status("Ничего не найдено")
            return

        for item in results:
            self._add_search_card(item)

        self.controller.set_status(f"Найдено {len(results)} модов")

    def _add_search_card(self, item: dict) -> None:
        """Добавляет карточку мода в результаты поиска."""
        card = ctk.CTkFrame(self.results_frame, corner_radius=10)
        card.pack(fill="x", pady=4, padx=2)

        # Левая часть: иконка + информация
        left_frame = ctk.CTkFrame(card, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        # Загрузка и отображение иконки
        icon_url = item.get("icon_url", "")
        icon_label = ctk.CTkLabel(left_frame, text="", width=48, height=48)
        icon_label.pack(side="left", padx=(0, 10))

        if icon_url:
            threading.Thread(
                target=lambda: self._load_icon(icon_url, icon_label, item["id"]),
                daemon=True,
            ).start()
        else:
            icon_label.configure(text="📦")

        info = ctk.CTkFrame(left_frame, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)

        title_row = ctk.CTkFrame(info, fg_color="transparent")
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=item["title"],
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left")

        src_badge = ctk.CTkLabel(
            title_row,
            text=item["source"].upper(),
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="white",
            fg_color="#1bd96a" if item["source"] == "modrinth" else "#f16436",
            corner_radius=4,
            width=70,
            height=18,
        )
        src_badge.pack(side="left", padx=(10, 0))

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

    def _load_icon(self, icon_url: str, label: ctk.CTkLabel, mod_id: str) -> None:
        """Загружает иконку мода из интернета."""
        try:
            import requests

            resp = requests.get(icon_url, timeout=5, stream=True)
            if resp.status_code == 200:
                img = Image.open(resp.raw)
                img = img.convert("RGBA")
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self._mod_images[mod_id] = tk_img
                root = self.winfo_toplevel()
                root.after(0, lambda lbl=label, i=tk_img: lbl.configure(image=i))
        except Exception as exc:
            logger.debug("Не удалось загрузить иконку {}: {}", icon_url, exc)
            root = self.winfo_toplevel()
            root.after(0, lambda lbl=label: lbl.configure(text="📦"))

    # ─────────────────── Установленные ───────────────────

    def _create_installed_tab(self) -> None:
        """Создаёт вкладку установленных модов."""
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
            command=lambda _: self._load_installed_mods(),
        )
        self.instance_combo.pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            top,
            text="🔄 Обновить",
            width=100,
            command=self._load_installed_mods,
        ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            top,
            text="📁 Добавить .jar",
            width=130,
            command=self._add_mod_from_file,
        ).pack(side="right")

        self.installed_list = ctk.CTkScrollableFrame(self.installed_tab)
        self.installed_list.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

    def _get_instance_names(self) -> list[str]:
        """Возвращает список имён инстансов."""
        instances = InstanceManager.list_instances()
        return [i.name for i in instances] if instances else ["Нет инстансов"]

    def _load_installed_mods(self) -> None:
        """Загружает список установленных модов."""
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

        mods_dir = instance.mods_dir
        if not mods_dir.exists():
            ctk.CTkLabel(
                self.installed_list,
                text="Папка mods пуста",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=30)
            return

        jars = sorted(mods_dir.glob("*.jar"), key=lambda p: p.name.lower())
        if not jars:
            ctk.CTkLabel(
                self.installed_list,
                text="Нет установленных модов",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=30)
            return

        for jar in jars:
            self._add_installed_mod_row(jar, instance)

        ctk.CTkLabel(
            self.installed_list,
            text=f"Всего модов: {len(jars)}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(pady=(10, 0))

    def _add_installed_mod_row(self, jar: Path, instance: Instance) -> None:
        """Добавляет строку установленного мода."""
        row = ctk.CTkFrame(self.installed_list, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(
            row,
            text=jar.name,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=5)

        size = jar.stat().st_size
        size_str = (
            f"{size / 1024 / 1024:.1f} MB"
            if size > 1024 * 1024
            else f"{size / 1024:.0f} KB"
        )
        ctk.CTkLabel(
            row,
            text=size_str,
            font=ctk.CTkFont(size=11),
            text_color="gray60",
        ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            row,
            text="🗑",
            width=36,
            height=28,
            fg_color="transparent",
            hover_color=("#aa3333", "#aa3333"),
            text_color=("#cc4444", "#ff6666"),
            command=lambda j=jar, i=instance: self._delete_mod(j, i),
        ).pack(side="right", padx=5)

    def _add_mod_from_file(self) -> None:
        """Добавляет мод из .jar файла."""
        name = self.instance_var.get()
        if not name or name == "Нет инстансов":
            self.controller.set_status("❌ Выберите инстанс")
            return

        instance = Instance.load(name)
        if instance is None:
            return

        paths = filedialog.askopenfilenames(
            filetypes=[("JAR файлы", "*.jar")],
            title="Выберите моды",
        )
        if not paths:
            return

        copied = 0
        for src in paths:
            try:
                dest = instance.mods_dir / Path(src).name
                import shutil

                shutil.copy2(src, dest)
                copied += 1
            except Exception as exc:
                logger.error("Ошибка копирования {}: {}", src, exc)

        self._load_installed_mods()
        self.controller.set_status(f"✅ Добавлено {copied} модов в {name}")

    def _delete_mod(self, jar: Path, instance: Instance) -> None:
        """Удаляет мод после подтверждения."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Удалить мод")
        dialog.geometry("350x130")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f'Удалить "{jar.name}"?',
            font=ctk.CTkFont(size=13),
        ).pack(pady=15)

        def confirm() -> None:
            try:
                jar.unlink()
                dialog.destroy()
                self._load_installed_mods()
                self.controller.set_status(f"🗑 {jar.name} удалён")
            except Exception as exc:
                logger.error("Ошибка удаления мода: {}", exc)

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

    # ─────────────────── Установка ──────────────────────

    def _show_install_dialog(self, item: dict) -> None:
        """Показывает диалог установки мода."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(item["title"])
        dialog.geometry("480x420")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=item["title"],
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 5))

        desc = item["description"]
        if len(desc) > 200:
            desc = desc[:200] + "..."
        ctk.CTkLabel(
            dialog,
            text=desc,
            font=ctk.CTkFont(size=12),
            wraplength=430,
            text_color="gray",
        ).pack(padx=20, pady=5)

        ctk.CTkLabel(
            dialog, text="Инстанс:", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 5))
        instances = InstanceManager.list_instances()
        names = [i.name for i in instances] if instances else ["Нет инстансов"]
        inst_var = ctk.StringVar(value=names[0])
        ctk.CTkComboBox(
            dialog, values=names, variable=inst_var, font=ctk.CTkFont(size=12)
        ).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            dialog,
            text="Версия Minecraft:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(10, 5))
        mc_ver = ctk.CTkEntry(dialog, placeholder_text="1.20.1", font=ctk.CTkFont(size=12))
        mc_ver.pack(fill="x", padx=20, pady=(0, 10))
        if self.version_filter.get().strip():
            mc_ver.insert(0, self.version_filter.get().strip())

        ctk.CTkLabel(
            dialog, text="Загрузчик:", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        loader_var = ctk.StringVar(value="fabric")
        ctk.CTkComboBox(
            dialog,
            values=["fabric", "forge", "quilt"],
            variable=loader_var,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=20, pady=(0, 10))
        if self.loader_filter.get() != "Любой":
            loader_var.set(self.loader_filter.get())

        status = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12))
        status.pack(pady=5)

        def on_install() -> None:
            iname = inst_var.get()
            if iname == "Нет инстансов":
                status.configure(text="❌ Создайте инстанс", text_color="red")
                return
            self._install_mod(
                item, iname, mc_ver.get().strip(), loader_var.get(), dialog, status
            )

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

    def _install_mod(
        self,
        item: dict,
        instance_name: str,
        game_version: str,
        loader: str,
        dialog: ctk.CTkToplevel,
        status: ctk.CTkLabel,
    ) -> None:
        """Скачивает и устанавливает мод."""
        instance = Instance.load(instance_name)
        if instance is None:
            status.configure(text="❌ Инстанс не найден", text_color="red")
            return

        status.configure(text="⏳ Поиск версии...", text_color="orange")
        dialog.update()

        def do_install() -> None:
            try:
                import requests

                if item["source"] == "modrinth":
                    # Получаем версию
                    url = f"https://api.modrinth.com/v2/project/{item['id']}/version"
                    params = {"game_versions": [game_version]} if game_version else {}
                    resp = requests.get(url, params=params, timeout=10)
                    resp.raise_for_status()
                    versions = resp.json()

                    # Ищем подходящую версию с правильным загрузчиком
                    target_loader = loader  # Используем loader как есть

                    file_info = None
                    for ver in versions:
                        loaders = ver.get("loaders", [])
                        if target_loader in loaders:
                            files = ver.get("files", [])
                            for f in files:
                                if f.get("primary", False):
                                    file_info = f
                                    break
                        if file_info:
                            break

                    if not file_info:
                        raise ValueError(f"Нет версии для {game_version}/{loader}")

                    # Скачиваем файл
                    download_url = file_info["url"]
                    filename = file_info["filename"]
                    dest = instance.mods_dir / filename

                    resp = requests.get(download_url, stream=True, timeout=60)
                    resp.raise_for_status()
                    with dest.open("wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)

                    fname = filename
                elif item["source"] == "curseforge":
                    api_key = getattr(self.controller.config, "curseforge_api_key", "")
                    if not api_key:
                        raise ValueError("CurseForge API ключ не задан")

                    # Получаем информацию о моде
                    url = f"https://api.curseforge.com/v1/mods/{item['id']}"
                    headers = {"X-API-Key": api_key}
                    resp = requests.get(url, headers=headers, timeout=10)
                    resp.raise_for_status()

                    # Получаем файлы
                    url = f"https://api.curseforge.com/v1/mods/{item['id']}/files"
                    params = {"game_version": game_version} if game_version else {}
                    resp = requests.get(url, headers=headers, params=params, timeout=10)
                    resp.raise_for_status()
                    files = resp.json()["data"]

                    # Ищем файл с правильным загрузчиком
                    loader_map = {"fabric": 4, "forge": 1, "quilt": 5}
                    target_loader_id = loader_map.get(loader)

                    file_info = None
                    for f in files:
                        if target_loader_id and f.get("mod_loader_type") == target_loader_id:
                            file_info = f
                            break

                    if not file_info:
                        raise ValueError(f"Нет версии для {game_version}/{loader}")

                    download_url = file_info.get("downloadUrl")
                    if not download_url:
                        raise ValueError("Нет URL для скачивания")

                    filename = file_info["fileName"]
                    dest = instance.mods_dir / filename

                    resp = requests.get(download_url, stream=True, timeout=60)
                    resp.raise_for_status()
                    with dest.open("wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)

                    fname = filename
                else:
                    raise ValueError(f"Неизвестный источник: {item['source']}")

                root = self.winfo_toplevel()
                root.after(0, lambda: status.configure(
                    text=f"✅ Установлен: {fname}", text_color="green"))
                root.after(0, lambda: self.controller.set_status(
                    f"Мод {item['title']} установлен в {instance_name}"))
            except Exception as exc:
                logger.error("Ошибка установки мода: {}", exc)
                root = self.winfo_toplevel()
                root.after(0, lambda err=str(exc): status.configure(
                    text=f"❌ Ошибка: {err}", text_color="red"))

        threading.Thread(target=do_install, daemon=True).start()

    def destroy(self) -> None:
        """Закрывает клиенты при уничтожении."""
        self._image_cache.clear()
        super().destroy()


