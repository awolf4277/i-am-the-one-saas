#!/usr/bin/env python3
"""Safely inspect or migrate WOLF OS data from SQLite to PostgreSQL.

The script never changes Render environment variables and never prints database
credentials. By default it performs an inspection only. Use --migrate to write.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
from typing import Any, Iterable
from urllib.parse import urlsplit

try:
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
except ImportError as exc:
    raise SystemExit(
        "psycopg is not installed. Run backend\\.venv\\Scripts\\python.exe "
        "-m pip install -r backend\\requirements.txt"
    ) from exc


DEFAULT_REPO = Path(r"X:\i-am-the-one-saas")
DEFAULT_SOURCE = (
    DEFAULT_REPO / "backend" / "data" / "i_am_the_one_saas.sqlite3"
)
PREFERRED_ORDER = [
    "stores",
    "products",
    "orders",
    "order_items",
    "setup_requests",
    "pipeline_deals",
    "pipeline_activity",
    "analytics_events",
]
SKIP_TABLES = {"sqlite_sequence"}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect or migrate WOLF OS SQLite data to PostgreSQL."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"SQLite source file (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--database-url",
        default="",
        help=(
            "PostgreSQL URL. Prefer setting DATABASE_URL in the current "
            "PowerShell session instead of passing it on the command line."
        ),
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Perform the migration. Without this flag, inspection only.",
    )
    parser.add_argument(
        "--replace-target",
        action="store_true",
        help=(
            "Allow replacement of existing target data. Required when any "
            "source-named target table already contains rows."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Rows inserted per batch (default: 500).",
    )
    return parser.parse_args()


def database_url(args: argparse.Namespace) -> str:
    value = str(args.database_url or os.getenv("DATABASE_URL", "")).strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]
    if not value:
        raise RuntimeError(
            "DATABASE_URL is missing. Set it only in the current PowerShell "
            "window using the Render External Database URL."
        )
    if not value.startswith(("postgresql://", "postgresql+")):
        raise RuntimeError("DATABASE_URL is not a PostgreSQL URL.")
    return value


def safe_target_label(url: str) -> str:
    parsed = urlsplit(url)
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    database = (parsed.path or "/unknown-database").lstrip("/")
    return f"{host}{port}/{database}"


def quote_sqlite_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def sqlite_connection(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 30000")
    return con


def source_schema(
    con: sqlite3.Connection,
) -> tuple[dict[str, str], list[str]]:
    tables: dict[str, str] = {}
    indexes: list[str] = []

    rows = con.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_master
        WHERE type IN ('table', 'index')
        ORDER BY
            CASE type WHEN 'table' THEN 0 ELSE 1 END,
            name
        """
    ).fetchall()

    for row in rows:
        object_type = str(row["type"])
        name = str(row["name"])
        ddl = row["sql"]

        if name.startswith("sqlite_") or name in SKIP_TABLES:
            continue
        if not ddl:
            continue

        if object_type == "table":
            tables[name] = str(ddl)
        elif object_type == "index":
            indexes.append(str(ddl))

    return tables, indexes


def ordered_tables(names: Iterable[str]) -> list[str]:
    name_set = set(names)
    ordered = [name for name in PREFERRED_ORDER if name in name_set]
    ordered.extend(sorted(name_set - set(ordered)))
    return ordered


def sqlite_count(con: sqlite3.Connection, table: str) -> int:
    row = con.execute(
        f"SELECT COUNT(*) AS count FROM {quote_sqlite_identifier(table)}"
    ).fetchone()
    return int(row["count"])


def sqlite_columns(con: sqlite3.Connection, table: str) -> list[str]:
    rows = con.execute(
        f"PRAGMA table_info({quote_sqlite_identifier(table)})"
    ).fetchall()
    return [str(row["name"]) for row in rows]


def postgres_tables(con: psycopg.Connection[Any]) -> set[str]:
    rows = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = current_schema()
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    ).fetchall()
    return {str(row["table_name"]) for row in rows}


def postgres_columns(
    con: psycopg.Connection[Any],
    table: str,
) -> list[str]:
    rows = con.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table,),
    ).fetchall()
    return [str(row["column_name"]) for row in rows]


def postgres_count(
    con: psycopg.Connection[Any],
    table: str,
) -> int:
    query = sql.SQL("SELECT COUNT(*) AS count FROM {}").format(
        sql.Identifier(table)
    )
    row = con.execute(query).fetchone()
    return int(row["count"])


def translate_sqlite_ddl(ddl: str) -> str:
    prepared = str(ddl).strip().rstrip(";")
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
    prepared = re.sub(
        r"\s+WITHOUT\s+ROWID\s*$",
        "",
        prepared,
        flags=re.IGNORECASE,
    )
    return prepared


def backup_sqlite(source: Path, repo: Path) -> Path:
    backup_dir = repo / "backups" / "postgres-migration"
    backup_dir.mkdir(parents=True, exist_ok=True)
    destination = backup_dir / f"sqlite-before-postgres-{utc_stamp()}.sqlite3"

    source_con = sqlite_connection(source)
    try:
        destination_con = sqlite3.connect(str(destination))
        try:
            source_con.backup(destination_con)
        finally:
            destination_con.close()
    finally:
        source_con.close()

    if not destination.exists() or destination.stat().st_size == 0:
        raise RuntimeError("SQLite backup was not created correctly.")

    return destination


def inspect(
    source_con: sqlite3.Connection,
    target_con: psycopg.Connection[Any],
    source_tables: list[str],
    target_label: str,
) -> None:
    target_names = postgres_tables(target_con)

    print("\n=== SQLITE SOURCE ===")
    for table in source_tables:
        print(f"{table:24} {sqlite_count(source_con, table):8} rows")

    print(f"\n=== POSTGRES TARGET: {target_label} ===")
    if not target_names:
        print("No application tables exist yet.")
    else:
        for table in source_tables:
            if table in target_names:
                print(
                    f"{table:24} "
                    f"{postgres_count(target_con, table):8} rows"
                )
            else:
                print(f"{table:24} MISSING")

    integrity = source_con.execute("PRAGMA integrity_check").fetchone()[0]
    print(f"\nSQLITE INTEGRITY: {integrity}")
    if str(integrity).lower() != "ok":
        raise RuntimeError(f"SQLite integrity check failed: {integrity}")


def target_has_rows(
    con: psycopg.Connection[Any],
    source_tables: list[str],
) -> tuple[bool, dict[str, int]]:
    existing = postgres_tables(con)
    counts: dict[str, int] = {}
    for table in source_tables:
        if table in existing:
            counts[table] = postgres_count(con, table)
    return any(count > 0 for count in counts.values()), counts


def drop_source_named_tables(
    con: psycopg.Connection[Any],
    source_tables: list[str],
) -> None:
    existing = postgres_tables(con)
    for table in reversed(source_tables):
        if table not in existing:
            continue
        query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
            sql.Identifier(table)
        )
        con.execute(query)


def create_schema(
    con: psycopg.Connection[Any],
    table_ddl: dict[str, str],
    index_ddl: list[str],
    source_tables: list[str],
) -> None:
    for table in source_tables:
        ddl = translate_sqlite_ddl(table_ddl[table])
        con.execute(ddl)

    for ddl in index_ddl:
        con.execute(translate_sqlite_ddl(ddl))


def row_values(
    row: sqlite3.Row,
    columns: list[str],
) -> tuple[Any, ...]:
    return tuple(row[column] for column in columns)


def copy_table(
    source_con: sqlite3.Connection,
    target_con: psycopg.Connection[Any],
    table: str,
    batch_size: int,
) -> int:
    source_cols = sqlite_columns(source_con, table)
    target_cols = set(postgres_columns(target_con, table))
    columns = [column for column in source_cols if column in target_cols]

    if not columns:
        raise RuntimeError(f"No matching columns found for table {table}.")

    select_query = (
        "SELECT "
        + ", ".join(quote_sqlite_identifier(column) for column in columns)
        + f" FROM {quote_sqlite_identifier(table)}"
    )

    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )

    cursor = source_con.execute(select_query)
    copied = 0

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        values = [row_values(row, columns) for row in rows]
        with target_con.cursor() as target_cursor:
            target_cursor.executemany(insert_query, values)
        copied += len(values)

    return copied


def reset_serial_sequence(
    con: psycopg.Connection[Any],
    table: str,
) -> None:
    columns = postgres_columns(con, table)
    if "id" not in columns:
        return

    sequence_row = con.execute(
        "SELECT pg_get_serial_sequence(%s, %s) AS sequence_name",
        (table, "id"),
    ).fetchone()
    sequence_name = sequence_row["sequence_name"] if sequence_row else None
    if not sequence_name:
        return

    max_query = sql.SQL("SELECT MAX({}) AS maximum FROM {}").format(
        sql.Identifier("id"),
        sql.Identifier(table),
    )
    maximum = con.execute(max_query).fetchone()["maximum"]

    if maximum is None:
        con.execute(
            "SELECT setval(%s::regclass, %s, %s)",
            (sequence_name, 1, False),
        )
    else:
        con.execute(
            "SELECT setval(%s::regclass, %s, %s)",
            (sequence_name, int(maximum), True),
        )


def migrate(
    source: Path,
    source_con: sqlite3.Connection,
    target_con: psycopg.Connection[Any],
    table_ddl: dict[str, str],
    index_ddl: list[str],
    source_tables: list[str],
    replace_target: bool,
    batch_size: int,
) -> None:
    integrity = source_con.execute("PRAGMA integrity_check").fetchone()[0]
    if str(integrity).lower() != "ok":
        raise RuntimeError(f"SQLite integrity check failed: {integrity}")

    has_rows, counts = target_has_rows(target_con, source_tables)
    if has_rows and not replace_target:
        details = ", ".join(
            f"{table}={count}" for table, count in counts.items() if count
        )
        raise RuntimeError(
            "Target already contains data. Inspection only is safe. "
            "After confirming this is the dedicated migration database, "
            "rerun with --migrate --replace-target. Existing rows: "
            + details
        )

    repo = DEFAULT_REPO
    try:
        repo = source.resolve().parents[2]
    except (IndexError, OSError):
        pass

    backup = backup_sqlite(source, repo)
    print(f"\nSQLITE BACKUP: {backup}")

    try:
        drop_source_named_tables(target_con, source_tables)
        create_schema(
            target_con,
            table_ddl,
            index_ddl,
            source_tables,
        )

        print("\n=== COPYING DATA ===")
        copied_counts: dict[str, int] = {}
        for table in source_tables:
            copied = copy_table(
                source_con,
                target_con,
                table,
                batch_size,
            )
            copied_counts[table] = copied
            print(f"{table:24} {copied:8} copied")

        for table in source_tables:
            reset_serial_sequence(target_con, table)

        print("\n=== VERIFYING COUNTS ===")
        mismatches: list[str] = []
        for table in source_tables:
            source_count = sqlite_count(source_con, table)
            target_count = postgres_count(target_con, table)
            status = "PASS" if source_count == target_count else "FAIL"
            print(
                f"{table:24} SQLite={source_count:<8} "
                f"Postgres={target_count:<8} {status}"
            )
            if source_count != target_count:
                mismatches.append(
                    f"{table}: SQLite={source_count}, "
                    f"Postgres={target_count}"
                )

        if mismatches:
            raise RuntimeError(
                "Row-count verification failed: " + "; ".join(mismatches)
            )

        target_con.commit()
    except Exception:
        target_con.rollback()
        raise

    print("\nMIGRATION VERIFIED: ALL TABLE COUNTS MATCH")
    print("Render API has NOT been switched to PostgreSQL.")


def main() -> int:
    args = parse_args()
    source = args.source.resolve()

    if args.batch_size < 1:
        raise RuntimeError("--batch-size must be at least 1.")
    if not source.exists():
        raise FileNotFoundError(f"SQLite source not found: {source}")

    url = database_url(args)
    target_label = safe_target_label(url)

    source_con = sqlite_connection(source)
    target_con: psycopg.Connection[Any] | None = None

    try:
        table_ddl, index_ddl = source_schema(source_con)
        source_tables = ordered_tables(table_ddl)

        if not source_tables:
            raise RuntimeError("No application tables found in SQLite.")

        print("WOLF OS SQLITE -> POSTGRESQL")
        print(f"SOURCE: {source}")
        print(f"TARGET: {target_label}")
        print("MODE:", "MIGRATE" if args.migrate else "INSPECT ONLY")

        target_con = psycopg.connect(
            url,
            row_factory=dict_row,
            connect_timeout=20,
        )

        if args.migrate:
            migrate(
                source,
                source_con,
                target_con,
                table_ddl,
                index_ddl,
                source_tables,
                args.replace_target,
                args.batch_size,
            )
        else:
            inspect(
                source_con,
                target_con,
                source_tables,
                target_label,
            )
            print("\nINSPECTION COMPLETE: NO DATA WAS CHANGED")

        return 0
    finally:
        source_con.close()
        if target_con is not None:
            target_con.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(
            f"\nERROR: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
