"""AI ассистент для QuantumLauncher.

Базовая заготовка для интеграции с Ollama/Llama.cpp.
В MVP режиме — локальные ответы на частые вопросы.
"""

from dataclasses import dataclass
from typing import Callable

from loguru import logger


@dataclass
class AssistantResponse:
    """Ответ AI ассистента."""

    text: str
    confidence: float = 1.0
    source: str = "local"


class LocalAssistant:
    """Локальный ассистент (без внешних зависимостей)."""

    # База знаний для быстрых ответов
    KNOWLEDGE_BASE: dict[str, str] = {
        "помощь": (
            "Доступные команды:\n"
            "• 'как установить мод' — инструкция по установке модов\n"
            "• 'как создать инстанс' — создание сборки Minecraft\n"
            "• 'оптимизация' — советы по повышению FPS\n"
            "• 'java' — настройка Java"
        ),
        "как установить мод": (
            "1. Перейдите на страницу 'Моды'\n"
            "2. Найдите нужный мод через поиск Modrinth\n"
            "3. Выберите версию, совместимую с вашим загрузчиком\n"
            "4. Скачайте .jar файл в папку mods вашего инстанса"
        ),
        "как создать инстанс": (
            "1. Откройте страницу 'Инстансы'\n"
            "2. Нажмите 'Создать'\n"
            "3. Укажите название, версию Minecraft и загрузчик\n"
            "4. Новая сборка появится в списке"
        ),
        "оптимизация": (
            "Советы по повышению FPS:\n"
            "• Установите мод Sodium (Fabric) или OptiFine\n"
            "• Выделите больше RAM в настройках (4-8 ГБ)\n"
            "• Используйте современную Java 17+\n"
            "• Закройте лишние программы перед запуском"
        ),
        "java": (
            "Настройка Java:\n"
            "• Рекомендуется Java 17 для Minecraft 1.18+\n"
            "• Java 8 для старых версий (1.16 и ниже)\n"
            "• Укажите путь к java.exe в настройках лаунчера\n"
            "• Минимум 2ГБ, рекомендуется 4-8ГБ RAM"
        ),
        "forge": (
            "Forge — модный загрузчик для Minecraft:\n"
            "1. На странице 'Версии' выберите нужную версию\n"
            "2. Нажмите 'Установить Forge'\n"
            "3. Дождитесь завершения установки\n"
            "4. Моды кладите в папку mods"
        ),
        "fabric": (
            "Fabric — лёгкий модный загрузчик:\n"
            "1. Быстрее Forge, меньше нагружает систему\n"
            "2. Многие оптимизационные моды только для Fabric\n"
            "3. Установка через страницу 'Версии'"
        ),
    }

    def __init__(self) -> None:
        self.history: list[dict[str, str]] = []

    def ask(self, question: str) -> AssistantResponse:
        """Задаёт вопрос ассистенту."""
        question_lower = question.lower().strip()
        logger.debug("AI вопрос: {}", question)

        # Прямое совпадение
        if question_lower in self.KNOWLEDGE_BASE:
            return AssistantResponse(
                text=self.KNOWLEDGE_BASE[question_lower],
                confidence=1.0,
            )

        # Частичное совпадение
        for key, answer in self.KNOWLEDGE_BASE.items():
            if key in question_lower or any(word in question_lower for word in key.split()):
                return AssistantResponse(text=answer, confidence=0.8)

        # Ответ по умолчанию
        default = (
            "Я пока не знаю ответа на этот вопрос.\n"
            "Попробуйте спросить о:\n"
            "• установке модов\n"
            "• создании инстанса\n"
            "• оптимизации\n"
            "• настройке Java\n"
            "• Forge / Fabric"
        )
        return AssistantResponse(text=default, confidence=0.3)

    def ask_stream(
        self,
        question: str,
        on_chunk: Callable[[str], None],
    ) -> None:
        """Потоковый ответ (имитация печатания)."""
        import time

        response = self.ask(question)
        for char in response.text:
            on_chunk(char)
            time.sleep(0.01)


class OllamaAssistant:
    """Ассистент через Ollama API (заготовка)."""

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434") -> None:
        self.model = model
        self.host = host

    def ask(self, question: str) -> AssistantResponse:
        """Запрос к Ollama."""
        # TODO: Реализовать через requests/aiohttp
        raise NotImplementedError("Ollama интеграция будет в следующей версии")
