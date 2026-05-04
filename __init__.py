"""QuantumLauncher - Next-generation Minecraft Launcher."""

from pathlib import Path


def _read_version() -> str:
    """Читает версию из pyproject.toml или возвращает fallback."""
    try:
        import tomllib

        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject.exists():
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            return data.get("project", {}).get("version", "0.1.0")
    except Exception:
        pass
    return "0.1.0"


__version__ = _read_version()
__author__ = "QuantumLauncher Team"
