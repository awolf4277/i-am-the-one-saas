# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.db import connect, now_iso

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health():
    con = connect()
    try:
        stores = con.execute("SELECT COUNT(*) AS count FROM stores").fetchone()["count"]
        products = con.execute("SELECT COUNT(*) AS count FROM products WHERE is_active = 1").fetchone()["count"]
        orders = con.execute("SELECT COUNT(*) AS count FROM orders").fetchone()["count"]
    finally:
        con.close()

    return jsonify(
        {
            "ok": True,
            "app": current_app.config["APP_NAME"],
            "brand": current_app.config["APP_BRAND"],
            "system": current_app.config["APP_SYSTEM"],
            "owner": current_app.config["APP_OWNER"],
            "version": "v3-saas-functional",
            "ts": now_iso(),
            "counts": {
                "stores": stores,
                "products": products,
                "orders": orders,
            },
        }
    )