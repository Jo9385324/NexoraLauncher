"""Страница управления шейдерами."""

import json
import os
from pathlib import Path

import customtkinter as ctk
import requests
from loguru import logger


class ShadersPage(ctk.CTkFrame):
    """Страница шейдеров и ресурспаков."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.instance_name = controller.config.last_version or "default"
        self.shaders_dir = (
            Path(os.environ.get("APPDATA", ""))
            / ".minecraft"
            / "shaderpacks"
        )
        self.shaders_dir.mkdir(parents=True, exist_ok=True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_header()
        self._create_search_section()
        self._create_shaders_list()

    def _create_header(self) -> None:
        """Создаёт заголовок."""
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        self.title_label = ctk.CTkLabel(
            self.header,
            text="Шейдеры",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header,
            text="Управление шейдерами и ресурспаками",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        self.subtitle_label.pack(anchor="w")

    def _create_search_section(self) -> None:
        """Создаёт секцию поиска."""
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Поиск шейдеров (например: BSL, Sildurs)",
            font=ctk.CTkFont(size=14),
        )
        self.search_entry.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.search_btn = ctk.CTkButton(
            self.search_frame,
            text="🔍 Поиск",
            command=self._search_shaders,
        )
        self.search_btn.grid(row=0, column=1, padx=(0, 20), pady=10)

    def _create_shaders_list(self) -> None:
        """Создаёт список шейдеров."""
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=2, column=0, sticky="nsew")

        self._load_installed_shaders()

    def _load_installed_shaders(self) -> None:
        """Загружает и отображает установленные шейдеры."""
        for widget in self.scroll.winfo_children():
            widget.destroy()

        if not self.shaders_dir.exists():
            label = ctk.CTkLabel(
                self.scroll,
                text="Папка шейдеров не найдена",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            )
            label.pack(pady=40)
            return

        shaders = list(self.shaders_dir.glob("*.zip"))
        if not shaders:
            label = ctk.CTkLabel(
                self.scroll,
                text="Нет установленных шейдеров\nНажмите 'Поиск' чтобы найти новые",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            )
            label.pack(pady=40)
            return

        for shader in shaders:
            self._add_shader_card(shader)

    def _add_shader_card(self, shader_path: Path) -> None:
        """Добавляет карточку шейдера."""
        card = ctk.CTkFrame(self.scroll)
        card.pack(fill="x", pady=5, padx=5)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        name_lbl = ctk.CTkLabel(
            info,
            text=shader_path.stem,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        name_lbl.pack(anchor="w")

        size_mb = shader_path.stat().st_size / (1024 * 1024)
        meta_lbl = ctk.CTkLabel(
            info,
            text=f"Размер: {size_mb:.1f} МБ",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        meta_lbl.pack(anchor="w")

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(side="right", padx=10, pady=10)

        use_btn = ctk.CTkButton(
            btns,
            text="▶ Использовать",
            width=100,
            height=30,
            command=lambda p=shader_path: self._use_shader(p),
        )
        use_btn.pack(side="left", padx=2)

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

    def _search_shaders(self) -> None:
        """Ищет шейдеры на Modrinth."""
        query = self.search_entry.get().strip()
        if not query:
            self.controller.set_status("Введите название шейдеров")
            return

        self.controller.set_status("🔍 Поиск шейдеров...")

        def search() -> None:
            try:
                url = "https://api.modrinth.com/v2/search"
                params = {
                    "query": query,
                    "index": "downloads",
                    "facets": '[{"values":["shaders"],"key":"categories"}]',
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

        import threading

        threading.Thread(target=search, daemon=True).start()

    def _show_search_results(self, results: list) -> None:
        """Показывает результаты поиска."""
        if not results:
            self.controller.set_status("Ничего не найдено")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Результаты поиска")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        for item in results[:10]:
            name = item.get("title", "Unknown")
            downloads = item.get("downloads", 0)
            project_id = item.get("slug", "")

            row = ctk.CTkFrame(scroll)
            row.pack(fill="x", pady=5)

            lbl = ctk.CTkLabel(
                row,
                text=f"{name} ⬇ {downloads:,}",
                font=ctk.CTkFont(size=13),
            )
            lbl.pack(side="left", fill="x", expand=True, padx=10)

            btn = ctk.CTkButton(
                row,
                text="⬇",
                width=40,
                command=lambda pid=project_id, n=name: self._download_shader(pid, n),
            )
            btn.pack(side="right", padx=5)

        ctk.CTkButton(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

    def _download_shader(self, project_id: str, name: str) -> None:
        """Скачивает шейдер с Modrinth."""
        self.controller.set_status(f"⬇ Скачивание {name}...")

        def download() -> None:
            try:
                # Получаем последнюю версию
                url = f"https://api.modrinth.com/v2/project/{project_id}/version"
                params = {"loaders": json.dumps(["fabric", "forge", "quilt"])}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                versions = response.json()
                if not versions:
                    raise ValueError("Нет версий")

                # Ищем версию с файлом шейдеров
                for v in versions:
                    files = v.get("files", [])
                    for f in files:
                        if f.get("primary", False) and f.get("url"):
                            download_url = f["url"]
                            filename = f["filename"]
                            self._save_shader(download_url, filename)
                            self.after(0, lambda: self.controller.set_status(f"✅ {name} скачан"))
                            return

                raise ValueError("Нет файлов для скачивания")
            except Exception as exc:
                logger.error("Ошибка скачивания шейдера: {}", exc)
                msg = str(exc)
                self.after(0, lambda m=msg: self.controller.set_status(f"❌ Ошибка: {m}"))

        import threading

        threading.Thread(target=download, daemon=True).start()

    def _save_shader(self, url: str, filename: str) -> None:
        """Сохраняет файл шейдера."""
        dest = self.shaders_dir / filename
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with dest.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("Шейдер сохранён: {}", dest)

    def _use_shader(self, shader_path: Path) -> None:
        """Активирует шейдер."""
        # Для использования шейдеров нужен Iris/Oculus или OptiFine
        # Пока просто копируем в папку шейдеров
        self.controller.set_status(f"Шейдер '{shader_path.stem}' готов к использованию")
        logger.info("Шейдер выбран: {}", shader_path.name)

    def _delete_shader(self, shader_path: Path) -> None:
        """Удаляет шейдер."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Подтверждение")
        dialog.geometry("350x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=f"Удалить шейдер '{shader_path.stem}'?",
            font=ctk.CTkFont(size=13),
        ).pack(pady=20)

        def confirm() -> None:
            shader_path.unlink()
            dialog.destroy()
            self._load_installed_shaders()
            self.controller.set_status(f"Шейдер '{shader_path.stem}' удалён")

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
