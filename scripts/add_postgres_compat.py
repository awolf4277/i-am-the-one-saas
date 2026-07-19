from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import shutil

ROOT = Path(r"X:\i-am-the-one-saas")
APP_INIT = ROOT / "backend" / "app" / "__init__.py"
ANALYTICS = ROOT / "backend" / "app" / "routes" / "analytics.py"
COMPAT = ROOT / "backend" / "app" / "db_compat.py"
REQUIREMENTS = ROOT / "backend" / "requirements.txt"

required = [APP_INIT, ANALYTICS, REQUIREMENTS]

for path in required:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup_dir = ROOT / "backups" / "postgres-compat" / timestamp
backup_dir.mkdir(parents=True, exist_ok=True)

for path in required:
    destination = backup_dir / path.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)

if COMPAT.exists():
    destination = backup_dir / COMPAT.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(COMPAT, destination)

compat_code = r'''# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
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
'''

COMPAT.write_text(compat_code, encoding="utf-8")

main = APP_INIT.read_text(encoding="utf-8-sig")

if (
    "from .db_compat import "
    "DatabaseConnection, connect_database, database_engine"
    not in main
):
    if "import sqlite3\n" not in main:
        raise RuntimeError("Could not find sqlite3 import in app/__init__.py.")

    main = main.replace(
        "import sqlite3\n",
        (
            "from .db_compat import "
            "DatabaseConnection, connect_database, database_engine\n"
        ),
        1,
    )

old_connection = """def connect(app: Flask) -> sqlite3.Connection:
    con = sqlite3.connect(app.config["DB_PATH"])
    con.row_factory = sqlite3.Row
    return con


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row["name"]) for row in rows}


def add_column(con: sqlite3.Connection, table: str, name: str, ddl: str) -> None:
"""

new_connection = """def connect(app: Flask) -> DatabaseConnection:
    return connect_database(app)


def table_columns(con: DatabaseConnection, table: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row["name"]) for row in rows}


def add_column(con: DatabaseConnection, table: str, name: str, ddl: str) -> None:
"""

if old_connection in main:
    main = main.replace(old_connection, new_connection, 1)
elif new_connection not in main:
    raise RuntimeError("Could not patch the main database connection helpers.")

main = main.replace(
    "def product_dict(row: sqlite3.Row) -> dict[str, Any]:",
    "def product_dict(row: Any) -> dict[str, Any]:",
)

old_config = """    app.config["JSON_SORT_KEYS"] = False
    app.config["DB_PATH"] = db_path_for(app)

    CORS"""

new_config = """    app.config["JSON_SORT_KEYS"] = False
    app.config["DB_PATH"] = db_path_for(app)
    app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", "").strip()
    app.config["DATABASE_ENGINE"] = database_engine(app)

    CORS"""

if old_config in main:
    main = main.replace(old_config, new_config, 1)
elif new_config not in main:
    raise RuntimeError("Could not add PostgreSQL application configuration.")

old_health = """                "db_path": app.config["DB_PATH"],
                "counts": counts,"""

new_health = """                "database_engine": app.config["DATABASE_ENGINE"],
                "db_path": (
                    "postgresql"
                    if app.config["DATABASE_ENGINE"] == "postgresql"
                    else app.config["DB_PATH"]
                ),
                "counts": counts,"""

if old_health in main:
    main = main.replace(old_health, new_health, 1)
elif new_health not in main:
    raise RuntimeError("Could not add database engine to the health response.")

sku_query = (
    '"SELECT * FROM products WHERE store_id = ? '
    'AND sku = ? LIMIT 1",'
)
sku_locked_query = (
    '"SELECT * FROM products WHERE store_id = ? '
    'AND sku = ? LIMIT 1 FOR UPDATE",'
)

if sku_locked_query not in main:
    if sku_query not in main:
        raise RuntimeError("Could not locate the active SKU checkout query.")

    main = main.replace(sku_query, sku_locked_query, 1)

id_query = (
    '"SELECT * FROM products WHERE store_id = ? '
    'AND id = ? LIMIT 1",'
)
id_locked_query = (
    '"SELECT * FROM products WHERE store_id = ? '
    'AND id = ? LIMIT 1 FOR UPDATE",'
)

if id_locked_query not in main:
    if id_query not in main:
        raise RuntimeError("Could not locate the active product-ID checkout query.")

    main = main.replace(id_query, id_locked_query, 1)

APP_INIT.write_text(main, encoding="utf-8")

analytics = ANALYTICS.read_text(encoding="utf-8-sig")

if (
    "from app.db_compat import DatabaseConnection, connect_database"
    not in analytics
):
    if "import sqlite3\n" not in analytics:
        raise RuntimeError("Could not find sqlite3 import in analytics.py.")

    analytics = analytics.replace(
        "import sqlite3\n",
        "from app.db_compat import DatabaseConnection, connect_database\n",
        1,
    )

old_analytics_connection = """def connect() -> sqlite3.Connection:
    con = sqlite3.connect(current_app.config["DB_PATH"])
    con.row_factory = sqlite3.Row
    return con
"""

new_analytics_connection = """def connect() -> DatabaseConnection:
    return connect_database(current_app)
"""

if old_analytics_connection in analytics:
    analytics = analytics.replace(
        old_analytics_connection,
        new_analytics_connection,
        1,
    )
elif new_analytics_connection not in analytics:
    raise RuntimeError("Could not patch the analytics database connection.")

analytics = analytics.replace(
    "def count_event(con: sqlite3.Connection, event_name: str) -> int:",
    "def count_event(con: DatabaseConnection, event_name: str) -> int:",
)
analytics = analytics.replace(
    (
        "def count_event_today("
        "con: sqlite3.Connection, event_name: str"
        ") -> int:"
    ),
    (
        "def count_event_today("
        "con: DatabaseConnection, event_name: str"
        ") -> int:"
    ),
)

ANALYTICS.write_text(analytics, encoding="utf-8")

requirements = REQUIREMENTS.read_text(
    encoding="utf-8-sig",
).splitlines()

if not any(line.strip().startswith("psycopg") for line in requirements):
    requirements.append("psycopg[binary]>=3.3,<4")

REQUIREMENTS.write_text(
    "\n".join(requirements).rstrip() + "\n",
    encoding="utf-8",
)

for path in [COMPAT, APP_INIT, ANALYTICS]:
    py_compile.compile(str(path), doraise=True)

print(f"Backup created: {backup_dir}")
print("Created backend/app/db_compat.py")
print("Patched active Flask database connections.")
print("Added PostgreSQL checkout row locking.")
print("Verified Python syntax.")
print("DATABASE_URL has NOT been enabled.")
