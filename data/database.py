"""Асинхронная база данных SQLite."""

from pathlib import Path
from typing import Any

import aiosqlite

from quantumlauncher.utils.paths import get_data_dir

DB_PATH = get_data_dir() / "quantumlauncher.db"


class Database:
    """Асинхронная обёртка над SQLite."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Устанавливает соединение с БД."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self) -> None:
        """Закрывает соединение."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def _create_tables(self) -> None:
        """Создаёт таблицы."""
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                version TEXT NOT NULL,
                mod_loader TEXT DEFAULT 'vanilla',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_played TIMESTAMP,
                play_count INTEGER DEFAULT 0
            )
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS mods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id INTEGER,
                name TEXT NOT NULL,
                version TEXT,
                mod_id TEXT,
                file_path TEXT,
                FOREIGN KEY (instance_id) REFERENCES instances(id)
            )
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        await self.commit()

    async def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> aiosqlite.Cursor:
        """Выполняет SQL запрос."""
        if not self._connection:
            raise RuntimeError("База данных не подключена")
        return await self._connection.execute(query, parameters)

    async def fetchall(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        """Выполняет запрос и возвращает все строки."""
        cursor = await self.execute(query, parameters)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetchone(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> dict[str, Any] | None:
        """Выполняет запрос и возвращает одну строку."""
        cursor = await self.execute(query, parameters)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def commit(self) -> None:
        """Фиксирует транзакцию."""
        if self._connection:
            await self._connection.commit()

    async def __aenter__(self) -> "Database":
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
