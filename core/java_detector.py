"""Автоопределение установленных Java на системе."""

import os
import platform
import re
import subprocess
from pathlib import Path
from typing import NamedTuple

from loguru import logger


class JavaInfo(NamedTuple):
    """Информация о найденной Java."""

    path: Path
    version: str
    vendor: str = ""


def _parse_java_version(output: str) -> tuple[str, str]:
    """Парсит версию и вендора из вывода `java -version`."""
    # OpenJDK / HotSpot: version "17.0.5" 2022-10-18
    m = re.search(r'version "?(\d+[\.\d_]*)"?', output)
    if not m:
        # newer openjdk: openjdk version "21" 2023-09-19
        m = re.search(r"version\s+\"(\d+[\.\d_]*)\"", output)
    version = m.group(1) if m else "unknown"

    lo = output.lower()
    vendor = ""
    if "openjdk" in lo:
        vendor = "OpenJDK"
    elif "hotspot" in lo:
        vendor = "HotSpot"
    elif "graalvm" in lo:
        vendor = "GraalVM"
    elif "microsoft" in lo:
        vendor = "Microsoft"
    elif "amazon" in lo or "corretto" in lo:
        vendor = "Amazon Corretto"

    return version, vendor


def get_java_info(java_path: str | Path) -> JavaInfo | None:
    """Возвращает информацию о Java по пути, или None если не валидна."""
    java_path = Path(java_path)
    exe = java_path if java_path.is_file() else java_path / "bin" / _java_exe()
    if not exe.exists():
        return None

    try:
        result = subprocess.run(
            [str(exe), "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # java -version пишет в stderr
        output = result.stderr or result.stdout
        if not output:
            return None

        version, vendor = _parse_java_version(output)
        return JavaInfo(path=exe.resolve(), version=version, vendor=vendor)
    except Exception as exc:
        logger.debug("Не удалось проверить Java {}: {}", exe, exc)
        return None


def _java_exe() -> str:
    """Имя исполняемого файла Java в зависимости от ОС."""
    return "java.exe" if platform.system() == "Windows" else "java"


def _env_paths() -> list[Path]:
    """Пути из переменных окружения."""
    paths: list[Path] = []
    for key in ("JAVA_HOME", "JDK_HOME", "JRE_HOME"):
        val = os.environ.get(key)
        if val:
            paths.append(Path(val))
    return paths


def _registry_paths() -> list[Path]:
    """Пути из реестра Windows."""
    if platform.system() != "Windows":
        return []

    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        return []

    paths: list[Path] = []
    keys_to_check = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Development Kit"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\Java Runtime Environment"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JDK"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JDK"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\JDK"),
    ]

    # на 64-битной Windows есть ещё WOW6432Node
    if platform.machine().endswith("64"):
        keys_to_check.extend([
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\JavaSoft\Java Development Kit"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\JavaSoft\Java Runtime Environment"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\JavaSoft\JDK"),
        ])

    for hkey, subkey in keys_to_check:
        try:
            with winreg.OpenKey(hkey, subkey) as key:
                i = 0
                while True:
                    try:
                        version_name = winreg.EnumKey(key, i)
                        i += 1
                        with winreg.OpenKey(key, version_name) as ver_key:
                            java_home, _ = winreg.QueryValueEx(ver_key, "JavaHome")
                            if java_home:
                                paths.append(Path(java_home))
                    except OSError:
                        break
        except OSError:
            continue

    return paths


def _common_paths() -> list[Path]:
    """Стандартные пути установки Java."""
    system = platform.system()
    candidates: list[Path] = []

    if system == "Windows":
        roots = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
            Path(os.environ.get("LocalAppData", "")) / "Programs",
        ]
        for root in roots:
            if root.exists():
                for sub in ("Java", "Eclipse Adoptium", "Microsoft", "Amazon Corretto", "BellSoft"):
                    candidates.append(root / sub)
    elif system == "Linux":
        candidates.append(Path("/usr/lib/jvm"))
        candidates.append(Path("/usr/java"))
        candidates.append(Path("/opt"))
    elif system == "Darwin":
        candidates.append(Path("/Library/Java/JavaVirtualMachines"))
        candidates.append(Path("/System/Library/Java/JavaVirtualMachines"))

    found: list[Path] = []
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            for item in candidate.iterdir():
                if item.is_dir():
                    # macOS .jdk bundles
                    if system == "Darwin" and item.suffix == ".jdk":
                        found.append(item / "Contents" / "Home")
                    else:
                        found.append(item)
        except PermissionError:
            continue
    return found


def _version_key(info: JavaInfo) -> tuple[int, ...]:
    """Ключ сортировки Java по версии (старшие первыми)."""
    parts = re.split(r"[._]", info.version)
    nums: list[int] = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            break
    return tuple(nums) if nums else (0,)


def find_all_java() -> list[JavaInfo]:
    """Находит все установленные Java на системе."""
    raw_paths: list[Path] = []
    raw_paths.extend(_env_paths())
    raw_paths.extend(_registry_paths())
    raw_paths.extend(_common_paths())

    # так же проверяем java из PATH
    path_env = os.environ.get("PATH", "")
    for directory in path_env.split(os.pathsep):
        p = Path(directory) / _java_exe()
        if p.exists():
            raw_paths.append(p.parent.parent)  # поднимаемся к JAVA_HOME

    seen: set[Path] = set()
    results: list[JavaInfo] = []

    for raw in raw_paths:
        # нормализуем: если указан на bin/java, поднимаемся к корню
        if raw.name == _java_exe() or (raw / _java_exe()).is_file():
            home = raw.parent.parent if raw.name == _java_exe() else raw
        else:
            home = raw

        if home in seen:
            continue
        seen.add(home)

        info = get_java_info(home)
        if info:
            results.append(info)
            logger.debug("Найдена Java {} в {}", info.version, info.path)

    results.sort(key=_version_key, reverse=True)
    return results


def find_best_java(min_version: int = 17) -> JavaInfo | None:
    """Находит лучшую подходящую Java (по умолчанию >= 17 для современных MC)."""
    all_java = find_all_java()  # уже отсортирована по убыванию версии

    for info in all_java:
        try:
            major = int(info.version.split(".")[0])
            if major >= min_version:
                return info
        except ValueError:
            continue
    # если ничего не подошло, возвращаем первую попавшуюся (самую новую)
    return all_java[0] if all_java else None
