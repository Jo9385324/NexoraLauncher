"""Страница AI чата-ассистента."""

import customtkinter as ctk
from loguru import logger

from quantumlauncher.ai.assistant import LocalAssistant


class AIChatPage(ctk.CTkFrame):
    """Страница AI помощника."""

    def __init__(self, parent: ctk.CTkFrame, controller: ctk.CTk) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.assistant = LocalAssistant()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._create_chat_area()
        self._create_input_area()

        # Приветственное сообщение
        welcome = "👋 Привет! Я AI помощник QuantumLauncher.\nЧем могу помочь?"
        self._add_message("assistant", welcome)

    def _create_chat_area(self) -> None:
        """Создаёт область чата."""
        self.chat_frame = ctk.CTkScrollableFrame(self)
        self.chat_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

    def _create_input_area(self) -> None:
        """Создаёт область ввода."""
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Задайте вопрос...",
            font=ctk.CTkFont(size=13),
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_entry.bind("<Return>", lambda _e: self._on_send())

        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Отправить",
            width=100,
            command=self._on_send,
        )
        self.send_btn.grid(row=0, column=1)

    def _on_send(self) -> None:
        """Обработчик отправки сообщения."""
        text = self.input_entry.get().strip()
        if not text:
            return

        self.input_entry.delete(0, "end")
        self._add_message("user", text)
        self.controller.set_status("AI думает...")

        try:
            response = self.assistant.ask(text)
            self._add_message("assistant", response.text)
            self.controller.set_status("Готов")
        except Exception as exc:
            logger.error("Ошибка AI: {}", exc)
            self._add_message("assistant", f"Ошибка: {exc}")
            self.controller.set_status("Ошибка AI")

    def _add_message(self, sender: str, text: str) -> None:
        """Добавляет сообщение в чат."""
        bubble = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        bubble.pack(fill="x", pady=5, padx=5)

        is_user = sender == "user"
        align = "e" if is_user else "w"
        bg_color = ("#3a7ebf", "#1f538d") if is_user else ("#e8e8e8", "#2b2b2b")
        text_color = "white" if is_user else None

        msg_frame = ctk.CTkFrame(bubble, fg_color=bg_color, corner_radius=12)
        msg_frame.pack(anchor=align, padx=10)

        label = ctk.CTkLabel(
            msg_frame,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color=text_color,
            wraplength=500,
            justify="left" if not is_user else "right",
        )
        label.pack(padx=12, pady=8)

        # Автопрокрутка вниз
        self.chat_frame.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0)
