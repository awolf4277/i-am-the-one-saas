# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

from flask import Blueprint, jsonify

from app.db import connect, row_to_dict, rows_to_dicts
from app.security import require_owner

orders_bp = Blueprint("orders", __name__, url_prefix="/api")


@orders_bp.get("/owner/orders")
@require_owner
def owner_orders():
    con = connect()
    try:
        rows = con.execute(
            """
            SELECT
                o.*,
                s.name AS store_name,
                COUNT(oi.id) AS item_count
            FROM orders o
            JOIN stores s ON s.slug = o.store_slug
            LEFT JOIN order_items oi ON oi.order_id = o.id
            GROUP BY o.id
            ORDER BY o.created_at DESC
            """
        ).fetchall()
    finally:
        con.close()

    return jsonify({"ok": True, "orders": rows_to_dicts(rows)})


@orders_bp.get("/owner/orders/<order_id>")
@require_owner
def owner_order_detail(order_id: str):
    con = connect()
    try:
        order = con.execute(
            """
            SELECT
                o.*,
                s.name AS store_name
            FROM orders o
            JOIN stores s ON s.slug = o.store_slug
            WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()

        if not order:
            return jsonify({"ok": False, "error": "ORDER_NOT_FOUND"}), 404

        items = con.execute(
            """
            SELECT *
            FROM order_items
            WHERE order_id = ?
            ORDER BY rowid ASC
            """,
            (order_id,),
        ).fetchall()
    finally:
        con.close()

    return jsonify({"ok": True, "order": row_to_dict(order), "items": rows_to_dicts(items)})