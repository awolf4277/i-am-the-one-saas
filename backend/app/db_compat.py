# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from flask import current_app


def _database_url(app: Any | None = None) -> str:
    configured = ""
    config = getattr(app, "config", None)

    if config is not None:
        configured = str(config.get("DATABASE_URL") or "").strip()

    value = configured or os.getenv("DATABASE_URL", "").strip()

    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://"):]

    return value


def database_engine(app: Any | None = None) -> str:
    return "postgresql" if _database_url(app) else "sqlite"


def _sqlite_path(app: Any | None = None) -> str:
    config = getattr(app, "config", None) or current_app.config
    value = str(config.get("DB_PATH") or "").strip()

    if not value:
        raise RuntimeError("DB_PATH is not configured.")

    path = Path(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def _qmarks_to_psycopg(sql: str) -> str:
    output: list[str] = []
    single = False
    double = False
    index = 0

    while index < len(sql):
        char = sql[index]

        if char == "'" and not double:
            output.append(char)

            if single and index + 1 < len(sql) and sql[index + 1] == "'":
                output.append("'")
                index += 2
                continue

            single = not single
            index += 1
            continue

        if char == '"' and not single:
            output.append(char)

            if double and index + 1 < len(sql) and sql[index + 1] == '"':
                output.append('"')
                index += 2
                continue

            double = not double
            index += 1
            continue

        output.append("%s" if char == "?" and not single and not double else char)
        index += 1

    return "".join(output)


class DatabaseConnection:
    def __init__(self, raw: Any, engine: str):
        self.raw = raw
        self.engine = engine

    @property
    def is_postgres(self) -> bool:
        return self.engine == "postgresql"

    def _prepare(self, sql: str) -> str:
        prepared = str(sql)

        if not self.is_postgres:
            return re.sub(
                r"\s+FOR\s+UPDATE\s*(?=;?\s*$)",
                "",
                prepared,
                flags=re.IGNORECASE,
            )

        prepared = re.sub(
            r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
            "BIGSERIAL PRIMARY KEY",
            prepared,
            flags=re.IGNORECASE,
        )
        prepared = re.sub(
            r"\bAUTOINCREMENT\b",
            "",
            prepared,
            flags=re.IGNORECASE,
        )

        if re.search(
            r"\bINSERT\s+OR\s+IGNORE\s+INTO\b",
            prepared,
            flags=re.IGNORECASE,
        ):
            prepared = re.sub(
                r"\bINSERT\s+OR\s+IGNORE\s+INTO\b",
                "INSERT INTO",
                prepared,
                count=1,
                flags=re.IGNORECASE,
            )

            stripped = prepared.rstrip()
            has_semicolon = stripped.endswith(";")

            if has_semicolon:
                stripped = stripped[:-1].rstrip()

            prepared = stripped + " ON CONFLICT DO NOTHING"

            if has_semicolon:
                prepared += ";"

        prepared = re.sub(
            r"\bORDER\s+BY\s+rowid\b",
            "ORDER BY id",
            prepared,
            flags=re.IGNORECASE,
        )

        return _qmarks_to_psycopg(prepared)

    def execute(
        self,
        sql: str,
        params: Iterable[Any] | None = None,
    ) -> Any:
        statement = str(sql).strip()

        if self.is_postgres:
            pragma = re.fullmatch(
                r"PRAGMA\s+table_info\(([^)]+)\)\s*;?",
                statement,
                flags=re.IGNORECASE,
            )

            if pragma:
                table = pragma.group(1).strip().strip('"').strip("'")
                return self.raw.execute(
                    """
                    SELECT column_name AS name
                    FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (table,),
                )

            if re.fullmatch(
                r"BEGIN\s+IMMEDIATE\s*;?",
                statement,
                flags=re.IGNORECASE,
            ):
                return self.raw.execute("SELECT 1")

        prepared = self._prepare(sql)

        if params is None:
            return self.raw.execute(prepared)

        return self.raw.execute(prepared, tuple(params))

    def commit(self) -> None:
        self.raw.commit()

    def rollback(self) -> None:
        self.raw.rollback()

    def close(self) -> None:
        self.raw.close()


def connect_database(app: Any | None = None) -> DatabaseConnection:
    url = _database_url(app)

    if url:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL requires psycopg. Install backend requirements."
            ) from exc

        raw = psycopg.connect(
            url,
            row_factory=dict_row,
            connect_timeout=15,
        )
        return DatabaseConnection(raw, "postgresql")

    raw = sqlite3.connect(_sqlite_path(app), timeout=30)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys = ON")
    raw.execute("PRAGMA busy_timeout = 30000")
    return DatabaseConnection(raw, "sqlite")
