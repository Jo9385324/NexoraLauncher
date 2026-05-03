"""Автоподбор JVM флагов для производительности Minecraft."""

from __future__ import annotations

import re


class JvmProfile:
    """Профиль JVM флагов."""

    DEFAULT = "default"
    PERFORMANCE = "performance"
    LOW = "low"


_PROFILES: dict[str, list[str]] = {
    JvmProfile.DEFAULT: [
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:+UseG1GC",
        "-XX:MaxGCPauseMillis=100",
        "-XX:+DisableExplicitGC",
        "-XX:+ParallelRefProcEnabled",
    ],
    JvmProfile.PERFORMANCE: [
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:+UseG1GC",
        "-XX:MaxGCPauseMillis=100",
        "-XX:+DisableExplicitGC",
        "-XX:+ParallelRefProcEnabled",
        "-XX:+UseStringDeduplication",
        "-XX:G1HeapRegionSize=16M",
        "-XX:+AlwaysPreTouch",
    ],
    JvmProfile.LOW: [
        "-XX:+UseSerialGC",
        "-XX:+DisableExplicitGC",
    ],
}


def _parse_mc_major(version_id: str) -> int:
    """Извлекает мажорную версию Minecraft из строки вида '1.20.1'."""
    # Убираем префиксы загрузчиков
    clean = version_id
    for prefix in ("forge-", "fabric-loader-", "quilt-loader-"):
        if prefix in clean:
            clean = clean.split("-")[-1]
            break

    m = re.match(r"1\.(\d+)", clean)
    if m:
        return int(m.group(1))
    # Для снапшотов или нестандартных версий
    try:
        parts = clean.split(".")
        if len(parts) >= 2 and parts[0] == "1":
            return int(parts[1])
    except ValueError:
        pass
    return 0


def get_jvm_flags(
    version_id: str,
    max_memory: int = 4096,
    min_memory: int = 512,
    profile: str = JvmProfile.DEFAULT,
) -> list[str]:
    """Возвращает список рекомендуемых JVM флагов.

    Args:
        version_id: ID версии Minecraft (например, '1.20.1').
        max_memory: Максимальная память в МБ.
        min_memory: Минимальная память в МБ.
        profile: Профиль оптимизации ('default', 'performance', 'low').
    """
    major = _parse_mc_major(version_id)

    flags: list[str] = [
        f"-Xmx{max_memory}M",
        f"-Xms{min_memory}M",
    ]

    # Для старых версий (< 1.16) достаточно минимума
    if major < 16:
        flags.append("-XX:+UseParallelGC")
        return flags

    profile_flags = _PROFILES.get(profile, _PROFILES[JvmProfile.DEFAULT])
    flags.extend(profile_flags)

    # Для Java 21+ и современных версий MC можно ZGC, но G1GC стабильнее для игр
    # Оставляем G1GC для всех профилей кроме low

    # Для слабых ПК урезаем память если слишком много
    if profile == JvmProfile.LOW and max_memory > 2048:
        flags[0] = "-Xmx2048M"

    return flags


def get_profile_description(profile: str) -> str:
    """Возвращает описание профиля на русском."""
    descriptions = {
        JvmProfile.DEFAULT: "Сбалансированный (G1GC, рекомендуется)",
        JvmProfile.PERFORMANCE: "Производительность (агрессивные флаги)",
        JvmProfile.LOW: "Слабый ПК (SerialGC, ≤2ГБ)",
    }
    return descriptions.get(profile, profile)
