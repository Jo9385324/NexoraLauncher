"""Управление версиями и запуском Minecraft."""

import subprocess
from typing import Callable

import minecraft_launcher_lib as mll
from loguru import logger

from quantumlauncher.core.java_detector import find_best_java
from quantumlauncher.core.jvm_flags import get_jvm_flags
from quantumlauncher.utils.paths import get_data_dir


class MinecraftManager:
    """Менеджер версий и запуска Minecraft."""

    def __init__(self) -> None:
        self.minecraft_dir = get_data_dir()
        self.minecraft_dir.mkdir(parents=True, exist_ok=True)

    def get_installed_versions(self) -> list[dict]:
        """Возвращает список установленных версий."""
        try:
            return mll.utils.get_installed_versions(str(self.minecraft_dir))
        except Exception as e:
            logger.error("Ошибка получения установленных версий: {}", e)
            return []

    def get_available_versions(self) -> list[dict]:
        """Возвращает список доступных для установки версий."""
        try:
            version_list = mll.utils.get_version_list()
            return [
                {
                    "id": v["id"],
                    "type": v["type"],
                    "release_time": v.get("releaseTime", ""),
                }
                for v in version_list
            ]
        except Exception as e:
            logger.error("Ошибка получения списка версий: {}", e)
            return []

    def _wrap_callback(
        self, callback: dict[str, Callable] | None
    ) -> mll.types.CallbackDict | None:
        """Преобразует dict callback в тип библиотеки."""
        if callback is None:
            return None
        return callback  # type: ignore[return-value]

    def install_version(
        self,
        version_id: str,
        callback: dict[str, Callable] | None = None,
    ) -> None:
        """Устанавливает версию Minecraft."""
        logger.info("Установка версии {}", version_id)
        mll.install.install_minecraft_version(
            version=version_id,
            minecraft_directory=str(self.minecraft_dir),
            callback=self._wrap_callback(callback),
        )
        logger.info("Версия {} установлена", version_id)

    def install_forge(
        self, version_id: str, callback: dict[str, Callable] | None = None
    ) -> str:
        """Устанавливает Forge для указанной версии."""
        logger.info("Установка Forge для {}", version_id)
        forge_version = mll.forge.find_forge_version(version_id)
        if forge_version is None:
            raise ValueError(f"Forge не найден для версии {version_id}")

        mll.forge.install_forge_version(
            forge_version,
            str(self.minecraft_dir),
            callback=self._wrap_callback(callback),
        )
        logger.info("Forge {} установлен", forge_version)
        return forge_version

    def install_fabric(
        self, version_id: str, callback: dict[str, Callable] | None = None
    ) -> str:
        """Устанавливает Fabric для указанной версии.

        Returns:
            ID версии для запуска (например "fabric-loader-0.14.21-1.20.1").
        """
        logger.info("Установка Fabric для {}", version_id)
        mll.fabric.install_fabric(
            minecraft_version=version_id,
            minecraft_directory=str(self.minecraft_dir),
            callback=self._wrap_callback(callback),
        )
        # Формируем ID как делает minecraft-launcher-lib
        loader_version = mll.fabric.get_latest_loader_version()
        version_str = f"fabric-loader-{loader_version}-{version_id}"
        logger.info("Fabric {} установлен", version_str)
        return version_str

    def _resolve_java_path(self, config_java_path: str) -> str:
        """Возвращает путь к Java: из конфига или автоопределённый."""
        if config_java_path and config_java_path != "java":
            return config_java_path
        info = find_best_java()
        if info:
            logger.info("Автоопределена Java {} в {}", info.version, info.path)
            return str(info.path)
        return "java"

    def get_java_command(self, config: dict) -> str:
        """Формирует Java команду с опциями."""
        java_path = self._resolve_java_path(config.get("java_path", ""))
        max_mem = config.get("max_memory", 4096)
        min_mem = config.get("min_memory", 512)

        options = [
            f"-Xmx{max_mem}M",
            f"-Xms{min_mem}M",
        ]

        return f'"{java_path}" {" ".join(options)}'

    def launch(
        self,
        version_id: str,
        username: str,
        options: dict | None = None,
        java_path: str = "",
        jvm_profile: str = "default",
        max_memory: int = 4096,
        min_memory: int = 512,
    ) -> subprocess.Popen:
        """Запускает Minecraft."""
        logger.info("Запуск Minecraft {} для пользователя {}", version_id, username)

        resolved_java = self._resolve_java_path(java_path)

        launch_options: dict = {
            "username": username,
            "uuid": "",
            "accessToken": "",
        }

        if options:
            launch_options.update(options)

        if resolved_java and resolved_java != "java":
            launch_options["executablePath"] = resolved_java

        # Автоподбор JVM флагов
        jvm_flags = get_jvm_flags(
            version_id=version_id,
            max_memory=max_memory,
            min_memory=min_memory,
            profile=jvm_profile,
        )
        launch_options.setdefault("jvmArguments", [])
        launch_options["jvmArguments"].extend(jvm_flags)
        logger.debug("JVM флаги: {}", " ".join(jvm_flags))

        command = mll.command.get_minecraft_command(
            version=version_id,
            minecraft_directory=str(self.minecraft_dir),
            options=launch_options,
        )

        logger.debug("Команда запуска: {}", " ".join(command))
        return subprocess.Popen(command, cwd=str(self.minecraft_dir))

    def get_version_info(self, version_id: str) -> dict:
        """Возвращает информацию о версии."""
        try:
            version_list = mll.utils.get_version_list()
            for v in version_list:
                if v["id"] == version_id:
                    return {
                        "id": v.get("id", version_id),
                        "type": v.get("type", "unknown"),
                        "release_time": v.get("releaseTime", ""),
                    }
            return {"id": version_id, "type": "unknown"}
        except Exception as exc:
            logger.error("Ошибка получения информации о версии {}: {}", version_id, exc)
            return {"id": version_id, "type": "unknown", "error": str(exc)}
