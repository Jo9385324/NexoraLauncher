"""Модуль оптимизаций производительности.

Использует Numba JIT для горячих участков кода.
При отсутствии Numba — fallback на чистый Python.
"""

from functools import wraps
from typing import Any, Callable

try:
    from numba import jit, njit

    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # Заглушки для совместимости
    def jit(*args: Any, **kwargs: Any) -> Callable:
        def decorator(func: Callable) -> Callable:
            return func

        return decorator

    njit = jit


def optional_njit(func: Callable) -> Callable:
    """Декоратор njit, который работает даже без Numba."""
    if NUMBA_AVAILABLE:
        return njit(func)
    return func


@optional_njit
def fast_checksum(data: bytes) -> int:
    """Быстрая контрольная сумма для данных.

    Numba-оптимизированная версия для проверки целостности файлов.
    """
    result = 0
    for i in range(len(data)):
        result = (result * 31 + data[i]) & 0xFFFFFFFF
    return result


@optional_njit
def fast_hash_string(s: str) -> int:
    """Быстрый хеш строки."""
    result = 0
    for char in s:
        result = (result * 31 + ord(char)) & 0xFFFFFFFF
    return result


@optional_njit
def interpolate_value(start: float, end: float, t: float) -> float:
    """Линейная интерполяция между двумя значениями.

    Используется для плавных анимаций и переходов.
    """
    return start + (end - start) * t


class PerformanceMonitor:
    """Монитор производительности операций."""

    def __init__(self) -> None:
        self.timings: dict[str, list[float]] = {}

    def time_operation(self, name: str) -> Callable:
        """Декоратор для замера времени выполнения."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                import time

                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.perf_counter() - start
                    if name not in self.timings:
                        self.timings[name] = []
                    self.timings[name].append(elapsed)

            return wrapper

        return decorator

    def get_stats(self, name: str) -> dict[str, float]:
        """Возвращает статистику по операции."""
        if name not in self.timings or not self.timings[name]:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

        timings = self.timings[name]
        return {
            "count": len(timings),
            "avg": sum(timings) / len(timings),
            "min": min(timings),
            "max": max(timings),
        }

    def report(self) -> dict[str, dict[str, float]]:
        """Возвращает отчёт по всем операциям."""
        return {name: self.get_stats(name) for name in self.timings}


# Глобальный монитор
perf_monitor = PerformanceMonitor()
