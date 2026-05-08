# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any

from flask import Blueprint, current_app, jsonify, request

products_bp = Blueprint("products", __name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12].upper()}"


def db_path() -> str:
    configured = str(current_app.config.get("DB_PATH") or os.getenv("DB_PATH") or "").strip()
    if configured:
        return configured

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_dir, "data", "i_am_the_one_saas_v3.sqlite3")


def connect() -> sqlite3.Connection:
    path = db_path()
    folder = os.path.dirname(path)

    if folder:
        os.makedirs(folder, exist_ok=True)

    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None

    return dict(row)


def require_owner(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        expected = str(
            os.getenv(
                "OWNER_API_TOKEN",
                current_app.config.get("OWNER_API_TOKEN", "")
            )
        ).strip()

        auth = request.headers.get("Authorization", "")
        token = ""

        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

        if not expected or token != expected:
            return jsonify({"ok": False, "error": "OWNER_AUTH_REQUIRED"}), 401

        return fn(*args, **kwargs)

    return wrapper


def normalize_product_payload(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "sku": str(raw.get("sku", "")).strip().upper(),
        "name": str(raw.get("name", "")).strip(),
        "category": str(raw.get("category", "Premium")).strip() or "Premium",
        "description": str(raw.get("description", "")).strip(),
        "price_cents": int(raw.get("price_cents") or 0),
        "stock": int(raw.get("stock") or 0),
        "image_url": str(raw.get("image_url", "")).strip(),
        "is_active": int(raw.get("is_active", 1)),
    }


@products_bp.get("/api/stores/<slug>/products")
def list_store_products(slug: str):
    store_slug = slug.strip().lower()

    con = connect()
    try:
        rows = con.execute(
            """
            SELECT
                id,
                store_slug,
                sku,
                name,
                category,
                description,
                price_cents,
                stock,
                image_url,
                is_active,
                created_at,
                updated_at
            FROM products
            WHERE store_slug = ?
              AND COALESCE(is_active, 1) = 1
            ORDER BY created_at ASC, name ASC
            """,
            (store_slug,),
        ).fetchall()

        return jsonify(
            {
                "ok": True,
                "store_slug": store_slug,
                "products": [row_to_dict(row) for row in rows],
            }
        )
    finally:
        con.close()


@products_bp.get("/api/owner/products")
@require_owner
def owner_products():
    con = connect()
    try:
        rows = con.execute(
            """
            SELECT
                p.id,
                p.store_slug,
                s.name AS store_name,
                p.sku,
                p.name,
                p.category,
                p.description,
                p.price_cents,
                p.stock,
                p.image_url,
                p.is_active,
                p.created_at,
                p.updated_at
            FROM products p
            LEFT JOIN stores s ON s.slug = p.store_slug
            ORDER BY p.store_slug ASC, p.created_at ASC, p.name ASC
            """
        ).fetchall()

        return jsonify(
            {
                "ok": True,
                "products": [row_to_dict(row) for row in rows],
            }
        )
    finally:
        con.close()


@products_bp.post("/api/stores/<slug>/products")
@require_owner
def create_product(slug: str):
    store_slug = slug.strip().lower()
    payload = request.get_json(silent=True) or {}
    data = normalize_product_payload(payload)

    if not data["sku"]:
        return jsonify({"ok": False, "error": "SKU_REQUIRED"}), 400

    if not data["name"]:
        return jsonify({"ok": False, "error": "NAME_REQUIRED"}), 400

    if data["price_cents"] < 0:
        return jsonify({"ok": False, "error": "PRICE_INVALID"}), 400

    if data["stock"] < 0:
        return jsonify({"ok": False, "error": "STOCK_INVALID"}), 400

    created_at = now_iso()
    product_id = new_id("prod")

    con = connect()
    try:
        store = con.execute(
            "SELECT slug FROM stores WHERE slug = ?",
            (store_slug,),
        ).fetchone()

        if not store:
            return jsonify({"ok": False, "error": "STORE_NOT_FOUND"}), 404

        existing = con.execute(
            """
            SELECT id
            FROM products
            WHERE store_slug = ?
              AND sku = ?
            """,
            (store_slug, data["sku"]),
        ).fetchone()

        if existing:
            return jsonify({"ok": False, "error": "SKU_ALREADY_EXISTS"}), 409

        con.execute(
            """
            INSERT INTO products (
                id,
                store_slug,
                sku,
                name,
                category,
                description,
                price_cents,
                stock,
                image_url,
                is_active,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                store_slug,
                data["sku"],
                data["name"],
                data["category"],
                data["description"],
                data["price_cents"],
                data["stock"],
                data["image_url"],
                data["is_active"],
                created_at,
                created_at,
            ),
        )

        con.commit()

        product = con.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()

        return jsonify({"ok": True, "product": row_to_dict(product)}), 201
    finally:
        con.close()


@products_bp.put("/api/stores/<slug>/products/<product_id>")
@require_owner
def update_product(slug: str, product_id: str):
    store_slug = slug.strip().lower()
    payload = request.get_json(silent=True) or {}

    allowed_fields = {
        "sku",
        "name",
        "category",
        "description",
        "price_cents",
        "stock",
        "image_url",
        "is_active",
    }

    updates: dict[str, Any] = {}

    for field in allowed_fields:
        if field in payload:
            value = payload[field]

            if field == "sku":
                value = str(value or "").strip().upper()
                if not value:
                    return jsonify({"ok": False, "error": "SKU_REQUIRED"}), 400

            if field in {"name", "category", "description", "image_url"}:
                value = str(value or "").strip()

            if field in {"price_cents", "stock", "is_active"}:
                value = int(value or 0)

            if field == "price_cents" and value < 0:
                return jsonify({"ok": False, "error": "PRICE_INVALID"}), 400

            if field == "stock" and value < 0:
                return jsonify({"ok": False, "error": "STOCK_INVALID"}), 400

            updates[field] = value

    if not updates:
        return jsonify({"ok": False, "error": "NO_UPDATES_PROVIDED"}), 400

    updates["updated_at"] = now_iso()

    set_sql = ", ".join([f"{field} = ?" for field in updates.keys()])
    values = list(updates.values()) + [product_id, store_slug]

    con = connect()
    try:
        existing = con.execute(
            """
            SELECT id
            FROM products
            WHERE id = ?
              AND store_slug = ?
            """,
            (product_id, store_slug),
        ).fetchone()

        if not existing:
            return jsonify({"ok": False, "error": "PRODUCT_NOT_FOUND"}), 404

        con.execute(
            f"""
            UPDATE products
            SET {set_sql}
            WHERE id = ?
              AND store_slug = ?
            """,
            values,
        )

        con.commit()

        product = con.execute(
            "SELECT * FROM products WHERE id = ? AND store_slug = ?",
            (product_id, store_slug),
        ).fetchone()

        return jsonify({"ok": True, "product": row_to_dict(product)})
    finally:
        con.close()


@products_bp.delete("/api/stores/<slug>/products/<product_id>")
@require_owner
def delete_product(slug: str, product_id: str):
    store_slug = slug.strip().lower()
    updated_at = now_iso()

    con = connect()
    try:
        existing = con.execute(
            """
            SELECT id
            FROM products
            WHERE id = ?
              AND store_slug = ?
            """,
            (product_id, store_slug),
        ).fetchone()

        if not existing:
            return jsonify({"ok": False, "error": "PRODUCT_NOT_FOUND"}), 404

        con.execute(
            """
            UPDATE products
            SET is_active = 0,
                updated_at = ?
            WHERE id = ?
              AND store_slug = ?
            """,
            (updated_at, product_id, store_slug),
        )

        con.commit()

        return jsonify({"ok": True, "deleted": product_id})
    finally:
        con.close()
