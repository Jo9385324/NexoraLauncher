"""Анализ crash-логов Minecraft."""

import re
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass
class CrashReport:
    """Результат анализа краш-лога."""

    cause: str
    description: str
    suggestion: str
    severity: str  # "critical", "warning", "info"
    raw_summary: str = ""


class CrashAnalyzer:
    """Анализатор crash-репортов Minecraft."""

    # Паттерны для определения причин
    PATTERNS = [
        (
            re.compile(r"java\.lang\.OutOfMemoryError", re.IGNORECASE),
            "Нехватка памяти",
            "Minecraft исчерпал выделенную оперативную память.",
            "Увеличьте максимальную память в настройках лаунчера "
            "(например, до 4096 МБ или выше). Также закройте другие "
            "тяжёлые программы перед запуском.",
            "critical",
        ),
        (
            re.compile(
                r"There is insufficient memory for the Java Runtime Environment",
                re.IGNORECASE,
            ),
            "Нехватка памяти в системе",
            "Системе не хватает RAM даже для работы JVM.",
            "Закройте все лишние приложения, увеличьте файл подкачки "
            "или добавьте оперативной памяти.",
            "critical",
        ),
        (
            re.compile(
                r"MissingModsException|Mod \w+ requires \w+|needs language provider",
                re.IGNORECASE,
            ),
            "Отсутствуют зависимости модов",
            "Один или несколько модов требуют другие моды или версию Forge/Fabric.",
            "Проверьте описание модов и установите все необходимые "
            "зависимости (например, Fabric API, Geckolib). Убедитесь, "
            "что версии модов соответствуют версии игры.",
            "warning",
        ),
        (
            re.compile(
                r"Mixin apply failed|MixinTransformerError|@Mixin annotation",
                re.IGNORECASE,
            ),
            "Конфликт миксинов",
            "Два или более модов пытаются изменить один и тот же код игры.",
            "Попробуйте удалить или обновить конфликтующие моды. "
            "Поищите в логе строки с 'Mixin apply failed' — там указаны моды-виновники.",
            "critical",
        ),
        (
            re.compile(
                r"LoaderExceptionModCrash|FMLModContainer|"
                r"Mod \w+ has been disabled|CONFLICT",
                re.IGNORECASE,
            ),
            "Конфликт модов или ошибка загрузки",
            "Мод вызвал исключение при загрузке или обнаружен конфликт.",
            "Проверьте совместимость модов, удалите недавно добавленные "
            "моды по одному, чтобы найти виновника. Обновите Forge/Fabric "
            "и сами моды до последних версий.",
            "critical",
        ),
        (
            re.compile(
                r"java\.lang\.UnsupportedClassVersionError",
                re.IGNORECASE,
            ),
            "Неверная версия Java",
            "Мод или ядро требуют более новую версию Java.",
            "Установите Java 17 (или 21 для Minecraft 1.20.5+) и укажите "
            "путь к ней в настройках лаунчера.",
            "critical",
        ),
        (
            re.compile(
                r"EXCEPTION_ACCESS_VIOLATION|sigsegv|"
                r"# C  \[ig\w+\.dll|# C  \[nv\w+\.dll",
                re.IGNORECASE,
            ),
            "Ошибка видеодрайвера или нативного кода",
            "Произошёл сбой в графическом драйвере или библиотеке GLFW/OpenAL.",
            "Обновите драйвер видеокарты (NVIDIA / AMD / Intel). "
            "Попробуйте отключить шейдеры, уменьшить настройки графики "
            "или удалить моды на оптимизацию графики.",
            "critical",
        ),
        (
            re.compile(
                r"GLFW error|Pixel format not accelerated|Unsupported display",
                re.IGNORECASE,
            ),
            "Проблема с графическим адаптером",
            "Не удалось создать окно OpenGL или подобрать пиксельный формат.",
            "Обновите драйверы видеокарты. Если используете ноутбук с двумя "
            "GPU, убедитесь, что игра запускается на дискретной видеокарте.",
            "warning",
        ),
        (
            re.compile(
                r"java\.net\.(UnknownHostException|ConnectException|"
                r"SocketTimeoutException)",
                re.IGNORECASE,
            ),
            "Проблема с сетью",
            "Не удалось подключиться к серверу Mojang или другому ресурсу.",
            "Проверьте подключение к интернету, отключите VPN/прокси, "
            "добавьте лаунчер в исключения фаервола.",
            "info",
        ),
        (
            re.compile(
                r"Could not find or load main class|NoClassDefFoundError",
                re.IGNORECASE,
            ),
            "Повреждённые файлы игры",
            "Java не может найти или загрузить необходимый класс.",
            "Попробуйте переустановить версию Minecraft через вкладку 'Версии'. "
            "Проверьте, что антивирус не удалил файлы игры.",
            "warning",
        ),
    ]

    @classmethod
    def analyze(cls, text: str) -> CrashReport:
        """Анализирует текст crash-лога и возвращает диагноз."""
        for pattern, cause, description, suggestion, severity in cls.PATTERNS:
            if pattern.search(text):
                # Извлекаем краткое резюме: первые 3 строки со словом error/exception/crash
                summary_lines = []
                for line in text.splitlines()[:50]:
                    if any(k in line.lower() for k in ("error", "exception", "crash", "caused by")):
                        summary_lines.append(line.strip())
                    if len(summary_lines) >= 3:
                        break
                raw = "\n".join(summary_lines)
                return CrashReport(
                    cause=cause,
                    description=description,
                    suggestion=suggestion,
                    severity=severity,
                    raw_summary=raw,
                )

        # Если ничего не подошло
        return CrashReport(
            cause="Неизвестная ошибка",
            description="Не удалось автоматически определить причину краша.",
            suggestion="Откройте полный crash-лог и поищите строки с 'Caused by' или 'Exception'. "
                       "Также можно обратиться за помощью к AI ассистенту в лаунчере.",
            severity="warning",
            raw_summary="",
        )

    @classmethod
    def analyze_file(cls, path: Path) -> CrashReport:
        """Анализирует файл crash-лога."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        return cls.analyze(text)


def get_latest_crash_report(minecraft_dir: Path) -> Path | None:
    """Возвращает путь к самому свежему crash-репорту."""
    crash_dir = minecraft_dir / "crash-reports"
    if not crash_dir.exists():
        return None

    reports = sorted(
        crash_dir.glob("crash-*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return reports[0] if reports else None


def get_latest_hs_err_pid(minecraft_dir: Path) -> Path | None:
    """Возвращает путь к самому свежему JVM crash log (hs_err_pid)."""
    logs = sorted(
        minecraft_dir.glob("hs_err_pid*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return logs[0] if logs else None


def analyze_latest_crash(minecraft_dir: Path) -> CrashReport | None:
    """Анализирует последний доступный crash-лог."""
    report = get_latest_crash_report(minecraft_dir)
    if report:
        logger.info("Анализ crash-репорта: {}", report.name)
        return CrashAnalyzer.analyze_file(report)

    hs_err = get_latest_hs_err_pid(minecraft_dir)
    if hs_err:
        logger.info("Анализ JVM crash log: {}", hs_err.name)
        return CrashAnalyzer.analyze_file(hs_err)

    return None
