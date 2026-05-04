# Launcher_Quantum
# QuantumLauncher

Следующее поколение лаунчера для Minecraft на Python.

## Возможности

- 🚀 Запуск Minecraft любых версий (Vanilla, Forge, Fabric, Quilt)
- 🤖 AI-помощник с базой знаний (Ollama интеграция в разработке)
- 🎨 Современный UI на CustomTkinter (тёмная/светлая тема, локализация RU/EN)
- 📁 Система инстансов — изолированные сборки с разными модами
- 🧩 Поиск модов через Modrinth API (с кэшированием)
- 🔍 Поиск модов через CurseForge API
- 🌐 Пинг серверов (MOTD, онлайн, задержка)
- ☕ Автоопределение и автозагрузка Java (Eclipse Adoptium)
- 🔐 Шифрование токенов Microsoft OAuth (привязка к машине)
- 📊 Анализ crash-логов с диагностикой
- ⚡ Асинхронные операции (aiohttp, потоки)
- 📝 Логирование в файл и консоль

## Установка

```bash
git clone <repo>
cd Quantym
pip install -e ".[dev]"
```

## Запуск

```bash
quantumlauncher
# или
python -m quantumlauncher.main
```

## Разработка

```bash
# Установка с dev-зависимостями
pip install -e ".[dev]"

# Линтер
ruff check quantumlauncher/ tests/

# Типизация
mypy quantumlauncher/ --ignore-missing-imports

# Тесты
pytest tests/ -v

# Сборка
python scripts/build.py
```

## Структура проекта

```
quantumlauncher/
├── core/
│   ├── minecraft.py         # Запуск/установка версий (Vanilla/Forge/Fabric)
│   ├── auth.py              # Авторизация (offline + MS OAuth)
│   ├── instance.py          # Система инстансов (сборок)
│   ├── skin.py              # Работа со скинами (Mojang API + рендер)
│   ├── crash_analyzer.py    # Анализ crash-логов
│   ├── java_detector.py     # Автоопределение Java
│   ├── java_downloader.py   # Автозагрузка Java
│   ├── jvm_flags.py         # Профили JVM флагов
│   ├── server_manager.py    # Управление серверами
│   ├── server_ping.py       # Пинг Minecraft серверов
│   └── discord_rpc.py       # Discord Rich Presence
├── ui/
│   ├── main_window.py       # Главное окно + навигация
│   └── pages/
│       ├── home_page.py         # Запуск игры + превью скина
│       ├── instances_page.py    # Управление сборками
│       ├── versions_page.py     # Установка версий (с прогрессом)
│       ├── mods_page.py         # Поиск и установка модов
│       ├── shaders_page.py      # Шейдеры
│       ├── servers_page.py      # Управление серверами
│       ├── ai_chat_page.py      # AI ассистент
│       └── settings_page.py     # Настройки
├── api/
│   ├── modrinth.py          # Асинхронный клиент Modrinth API (с кэшем)
│   └── curseforge.py        # Асинхронный клиент CurseForge API (с кэшем)
├── ai/
│   └── assistant.py         # Локальный AI + Ollama заготовка
├── data/
│   └── database.py          # Асинхронная SQLite
├── utils/
│   ├── paths.py             # Пути к директориям
│   ├── config.py            # Конфигурация приложения (с валидацией)
│   ├── crypto.py            # Шифрование токенов
│   ├── i18n.py              # Локализация (RU/EN)
│   └── perf.py              # Оптимизации (Numba JIT)
└── _fastcore.pyx            # Cython-модуль (опционально)
```

## Тесты

```bash
pytest tests/ -v
```

Покрытие:
- Конфигурация (сохранение/загрузка, валидация, шифрование)
- Пути и директории
- Инстансы (создание, удаление, список)
- Modrinth API (поиск модов)
- Авторизация (offline, MS OAuth)
- Анализ crash-логов

## Roadmap MVP

- [x] Базовый UI на CustomTkinter
- [x] Запуск Minecraft (Vanilla)
- [x] Установка версий с прогрессом
- [x] Система инстансов
- [x] Поиск модов через Modrinth (с кэшем)
- [x] Поиск модов через CurseForge (заготовка)
- [x] AI ассистент (локальный)
- [x] Microsoft OAuth авторизация (с шифрованием токенов)
- [x] Установка Forge/Fabric
- [x] Скачивание и установка модов
- [x] 2D превью скинов (с debounce)
- [x] Пинг серверов
- [x] Автозагрузка Java
- [x] Локализация (RU/EN)
- [x] Анализ crash-логов
- [x] CI/CD (GitHub Actions)
- [ ] Облачная синхронизация
- [ ] Полноценный 3D рендер скинов
- [ ] Полноценная Ollama интеграция

## Лицензия

MIT
## проект в ранний бета версии!
##[requirements.txt]
-minecraft-launcher-lib>=6.0
-customtkinter>=5.2
-Pillow>=10.0
-aiohttp>=3.9
-aiosqlite>=0.19
-pydantic>=2.0
-platformdirs>=4.0
-loguru>=0.7
-cryptography>=42.0
