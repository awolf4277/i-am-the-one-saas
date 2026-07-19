# Copyright ? 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import os
from app.db_compat import DatabaseConnection, connect_database
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, current_app, jsonify, request

analytics_bp = Blueprint("analytics", __name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_prefix() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def connect() -> DatabaseConnection:
    return connect_database(current_app)


def init_analytics_db() -> None:
    con = connect()
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                path TEXT DEFAULT '',
                source TEXT DEFAULT '',
                user_agent TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        con.commit()
    finally:
        con.close()


def owner_authorized() -> bool:
    expected = os.getenv("OWNER_TOKEN", "wolf-owner-local-token").strip()

    auth = request.headers.get("Authorization", "").strip()
    token = ""

    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()

    if not token:
        token = request.headers.get("X-Owner-Token", "").strip()

    return bool(expected and token and token == expected)


def count_event(con: DatabaseConnection, event_name: str) -> int:
    row = con.execute(
        "SELECT COUNT(*) AS total FROM analytics_events WHERE event_name = ?",
        (event_name,),
    ).fetchone()

    return int(row["total"] or 0)


def count_event_today(con: DatabaseConnection, event_name: str) -> int:
    row = con.execute(
        """
        SELECT COUNT(*) AS total
        FROM analytics_events
        WHERE event_name = ?
          AND created_at LIKE ?
        """,
        (event_name, f"{today_prefix()}%"),
    ).fetchone()

    return int(row["total"] or 0)


@analytics_bp.post("/api/analytics/event")
def create_analytics_event():
    init_analytics_db()

    data: dict[str, Any] = request.get_json(silent=True) or {}

    event_name = str(data.get("event_name") or data.get("event") or "").strip()
    path = str(data.get("path") or "").strip()
    source = str(data.get("source") or "frontend").strip()

    allowed_events = {
        "landing_page_visit",
        "store_visit",
        "owner_visit",
        "setup_request_submit",
        "demo_pitch_copy",
    }

    if event_name not in allowed_events:
        return jsonify({"ok": False, "error": "Invalid analytics event."}), 400

    user_agent = request.headers.get("User-Agent", "")[:300]

    con = connect()
    try:
        con.execute(
            """
            INSERT INTO analytics_events (
                event_name,
                path,
                source,
                user_agent,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_name, path, source, user_agent, now_iso()),
        )
        con.commit()
    finally:
        con.close()

    return jsonify({"ok": True, "event_name": event_name})


@analytics_bp.get("/api/owner/analytics")
def owner_analytics():
    if not owner_authorized():
        return jsonify({"ok": False, "error": "Unauthorized owner request."}), 401

    init_analytics_db()

    con = connect()
    try:
        total_visits = count_event(con, "landing_page_visit") + count_event(con, "store_visit")
        visits_today = count_event_today(con, "landing_page_visit") + count_event_today(con, "store_visit")

        landing_visits = count_event(con, "landing_page_visit")
        store_visits = count_event(con, "store_visit")
        owner_visits = count_event(con, "owner_visit")
        setup_submits = count_event(con, "setup_request_submit")
        demo_pitch_copies = count_event(con, "demo_pitch_copy")

        conversion_rate = 0.0
        if total_visits:
            conversion_rate = round((setup_submits / total_visits) * 100, 2)

        return jsonify(
            {
                "ok": True,
                "total_visits": total_visits,
                "visits_today": visits_today,
                "landing_visits": landing_visits,
                "store_visits": store_visits,
                "owner_visits": owner_visits,
                "setup_request_submits": setup_submits,
                "demo_pitch_copies": demo_pitch_copies,
                "conversion_rate": conversion_rate,
            }
        )
    finally:
        con.close()
