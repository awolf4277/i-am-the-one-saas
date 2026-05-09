# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import sqlite3
from flask import Blueprint, current_app, jsonify

products_bp = Blueprint("products", __name__)


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(current_app.config["DB_PATH"])
    con.row_factory = sqlite3.Row
    return con


@products_bp.get("/api/stores/<slug>/products")
def store_products(slug: str):
    con = connect()
    try:
        store = con.execute(
            "SELECT * FROM stores WHERE slug = ?",
            (slug,),
        ).fetchone()

        if not store:
            return jsonify({"ok": False, "error": f"Store not found: {slug}"}), 404

        products = con.execute(
            """
            SELECT id, store_id, sku, name, category, description, price_cents, stock, image_url
            FROM products
            WHERE store_id = ?
            ORDER BY category, name
            """,
            (store["id"],),
        ).fetchall()

        return jsonify(
            {
                "ok": True,
                "store": dict(store),
                "count": len(products),
                "products": [dict(row) for row in products],
            }
        )
    finally:
        con.close()
