# Copyright Â© 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.db import connect, new_id, now_iso, row_to_dict, rows_to_dicts
from app.security import require_owner

stores_bp = Blueprint("stores", __name__, url_prefix="/api")


@stores_bp.get("/stores")
def list_stores():
    con = connect()
    try:
        rows = con.execute(
            """
            SELECT
                s.*,
                COUNT(p.id) AS product_count
            FROM stores s
            LEFT JOIN products p
                ON p.store_slug = s.slug
                AND p.is_active = 1
            GROUP BY s.id
            ORDER BY s.created_at ASC
            """
        ).fetchall()
    finally:
        con.close()

    return jsonify({"ok": True, "stores": rows_to_dicts(rows)})


@stores_bp.get("/stores/<slug>")
def get_store(slug: str):
    con = connect()
    try:
        row = con.execute(
            """
            SELECT
                s.*,
                COUNT(p.id) AS product_count
            FROM stores s
            LEFT JOIN products p
                ON p.store_slug = s.slug
                AND p.is_active = 1
            WHERE s.slug = ?
            GROUP BY s.id
            """,
            (slug,),
        ).fetchone()
    finally:
        con.close()

    store = row_to_dict(row)
    if not store:
        return jsonify({"ok": False, "error": "STORE_NOT_FOUND"}), 404

    return jsonify({"ok": True, "store": store})


@stores_bp.get("/owner/stores")
@require_owner
def owner_stores():
    return list_stores()


@stores_bp.post("/stores")
@require_owner
def create_store():
    data = request.get_json(silent=True) or {}

    slug = str(data.get("slug", "")).strip().lower()
    name = str(data.get("name", "")).strip()
    owner_name = str(data.get("owner_name", "Andrew Wolverton")).strip()
    status = str(data.get("status", "active")).strip() or "active"
    plan = str(data.get("plan", "v3-saas")).strip() or "v3-saas"
    currency = str(data.get("currency", "USD")).strip() or "USD"

    if not slug or not name:
        return jsonify({"ok": False, "error": "SLUG_AND_NAME_REQUIRED"}), 400

    created = now_iso()
    store_id = new_id("store")

    con = connect()
    try:
        con.execute(
            """
            INSERT INTO stores
            (id, slug, name, owner_name, status, plan, currency, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (store_id, slug, name, owner_name, status, plan, currency, created, created),
        )
        con.commit()

        row = con.execute("SELECT * FROM stores WHERE id = ?", (store_id,)).fetchone()
    except Exception as exc:
        con.rollback()
        return jsonify({"ok": False, "error": "STORE_CREATE_FAILED", "message": str(exc)}), 400
    finally:
        con.close()

    return jsonify({"ok": True, "store": row_to_dict(row)}), 201


@stores_bp.put("/stores/<slug>")
@require_owner
def update_store(slug: str):
    data = request.get_json(silent=True) or {}

    allowed = ["name", "owner_name", "status", "plan", "currency"]
    updates = []
    values = []

    for field in allowed:
        if field in data:
            updates.append(f"{field} = ?")
            values.append(str(data.get(field, "")).strip())

    if not updates:
        return jsonify({"ok": False, "error": "NO_FIELDS_TO_UPDATE"}), 400

    updates.append("updated_at = ?")
    values.append(now_iso())
    values.append(slug)

    con = connect()
    try:
        con.execute(f"UPDATE stores SET {', '.join(updates)} WHERE slug = ?", values)
        con.commit()

        row = con.execute("SELECT * FROM stores WHERE slug = ?", (slug,)).fetchone()
    finally:
        con.close()

    store = row_to_dict(row)
    if not store:
        return jsonify({"ok": False, "error": "STORE_NOT_FOUND"}), 404

    return jsonify({"ok": True, "store": store})

