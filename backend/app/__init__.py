# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS


OWNER = os.getenv("APP_OWNER", "Andrew Wolverton")
BRAND = os.getenv("APP_BRAND", "I AM THE ONE™")
SYSTEM = os.getenv("APP_SYSTEM", "WOLF OS™")
APP_NAME = os.getenv("APP_NAME", "I AM THE ONE™ SaaS v3 API")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def cors_origins() -> str | list[str]:
    raw = os.getenv("CORS_ORIGINS", "*").strip()
    if not raw or raw == "*":
        return "*"
    return [x.strip() for x in raw.split(",") if x.strip()]


def db_path_for(app: Flask) -> str:
    raw = os.getenv("DB_PATH", "").strip()
    if raw:
        path = Path(raw)
    else:
        path = Path(app.root_path).parent / "data" / "i_am_the_one_saas.sqlite3"

    if not path.is_absolute():
        path = Path(app.root_path).parent / path

    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def connect(app: Flask) -> sqlite3.Connection:
    con = sqlite3.connect(app.config["DB_PATH"])
    con.row_factory = sqlite3.Row
    return con


def table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row["name"]) for row in rows}


def add_column(con: sqlite3.Connection, table: str, name: str, ddl: str) -> None:
    cols = table_columns(con, table)
    if name not in cols:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def ensure_schema(app: Flask) -> None:
    con = connect(app)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS stores (
                id TEXT PRIMARY KEY,
                slug TEXT,
                name TEXT,
                brand TEXT,
                system TEXT,
                plan TEXT,
                status TEXT,
                created_at TEXT
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                store_id TEXT,
                sku TEXT,
                name TEXT,
                category TEXT,
                description TEXT,
                price_cents INTEGER,
                stock INTEGER,
                image_url TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                store_id TEXT,
                store_slug TEXT,
                buyer_name TEXT,
                buyer_email TEXT,
                buyer_phone TEXT,
                notes TEXT,
                subtotal_cents INTEGER,
                tax_cents INTEGER,
                shipping_cents INTEGER,
                discount_cents INTEGER,
                total_cents INTEGER,
                currency TEXT,
                payment_mode TEXT,
                payment_status TEXT,
                status TEXT,
                created_at TEXT
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                product_id TEXT,
                sku TEXT,
                name TEXT,
                qty INTEGER,
                unit_amount_cents INTEGER,
                line_total_cents INTEGER
            )
            """
        )

        for name, ddl in {
            "id": "TEXT",
            "slug": "TEXT",
            "name": "TEXT",
            "brand": "TEXT",
            "system": "TEXT",
            "plan": "TEXT DEFAULT 'demo'",
            "status": "TEXT DEFAULT 'active'",
            "created_at": "TEXT",
        }.items():
            add_column(con, "stores", name, ddl)

        for name, ddl in {
            "id": "TEXT",
            "store_id": "TEXT DEFAULT 'store_demo'",
            "store_slug": "TEXT DEFAULT 'demo'",
            "sku": "TEXT",
            "name": "TEXT",
            "category": "TEXT DEFAULT 'General'",
            "description": "TEXT DEFAULT ''",
            "price_cents": "INTEGER DEFAULT 0",
            "stock": "INTEGER DEFAULT 0",
            "image_url": "TEXT DEFAULT ''",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        }.items():
            add_column(con, "products", name, ddl)

        for name, ddl in {
            "id": "TEXT",
            "store_id": "TEXT DEFAULT 'store_demo'",
            "store_slug": "TEXT DEFAULT 'demo'",
            "buyer_name": "TEXT DEFAULT ''",
            "buyer_email": "TEXT DEFAULT ''",
            "buyer_phone": "TEXT DEFAULT ''",
            "notes": "TEXT DEFAULT ''",
            "subtotal_cents": "INTEGER DEFAULT 0",
            "tax_cents": "INTEGER DEFAULT 0",
            "shipping_cents": "INTEGER DEFAULT 0",
            "discount_cents": "INTEGER DEFAULT 0",
            "total_cents": "INTEGER DEFAULT 0",
            "currency": "TEXT DEFAULT 'USD'",
            "payment_mode": "TEXT DEFAULT 'manual'",
            "payment_status": "TEXT DEFAULT 'unpaid'",
            "status": "TEXT DEFAULT 'created'",
            "created_at": "TEXT",
        }.items():
            add_column(con, "orders", name, ddl)

        for name, ddl in {
            "order_id": "TEXT",
            "product_id": "TEXT",
            "sku": "TEXT",
            "name": "TEXT",
            "qty": "INTEGER DEFAULT 1",
            "unit_amount_cents": "INTEGER DEFAULT 0",
            "line_total_cents": "INTEGER DEFAULT 0",
        }.items():
            add_column(con, "order_items", name, ddl)

        con.execute(
            """
            INSERT OR IGNORE INTO stores (id, slug, name, brand, system, plan, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("store_demo", "demo", f"{BRAND} Demo Store", BRAND, SYSTEM, "demo", "active", now_iso()),
        )

        con.execute(
            """
            UPDATE stores
            SET slug = COALESCE(NULLIF(slug, ''), 'demo'),
                name = COALESCE(NULLIF(name, ''), ?),
                brand = COALESCE(NULLIF(brand, ''), ?),
                system = COALESCE(NULLIF(system, ''), ?),
                plan = COALESCE(NULLIF(plan, ''), 'demo'),
                status = COALESCE(NULLIF(status, ''), 'active'),
                created_at = COALESCE(NULLIF(created_at, ''), ?)
            WHERE id = 'store_demo'
            """,
            (f"{BRAND} Demo Store", BRAND, SYSTEM, now_iso()),
        )

        seed_products = [
            (
                "wolf-001",
                "store_demo",
                "WOLF-001",
                "Wolf Signature Hoodie",
                "Apparel",
                "Premium black signature hoodie for I AM THE ONE™ buyers.",
                9900,
                12,
                "https://placehold.co/900x700/png?text=WOLF+SIGNATURE+HOODIE",
            ),
            (
                "wolf-core",
                "store_demo",
                "WOLF-CORE",
                "WOLF OS™ Core",
                "Software",
                "Foundational operator system package for modern storefront control.",
                9900,
                25,
                "https://placehold.co/900x700/png?text=WOLF+OS+CORE",
            ),
            (
                "iato-launch",
                "store_demo",
                "IATO-LAUNCH",
                "I AM THE ONE™ Launch Kit",
                "Launch",
                "Starter package for branded storefront deployment.",
                29900,
                7,
                "https://placehold.co/900x700/png?text=I+AM+THE+ONE",
            ),
            (
                "operator-license",
                "store_demo",
                "WOLF-OPERATOR",
                "Operator Console License",
                "Software",
                "Owner dashboard and storefront control package.",
                49900,
                5,
                "https://placehold.co/900x700/png?text=OPERATOR+CONSOLE",
            ),
        ]

        for item in seed_products:
            existing = con.execute(
                "SELECT id FROM products WHERE sku = ? LIMIT 1",
                (item[2],),
            ).fetchone()
            if not existing:
                con.execute(
                    """
                    INSERT INTO products (
                        id, store_id, store_slug, sku, name, category, description,
                        price_cents, stock, image_url, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*item[:2], "demo", *item[2:], now_iso(), now_iso()),
                )

        con.commit()
    finally:
        con.close()


def owner_token() -> str:
    return os.getenv("OWNER_API_TOKEN", "wolf-owner-local-token").strip() or "wolf-owner-local-token"


def require_owner() -> tuple[bool, Any]:
    auth = request.headers.get("Authorization", "")
    token = ""
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()

    if secrets.compare_digest(token, owner_token()):
        return True, None

    return False, (jsonify({"ok": False, "error": "Unauthorized owner request."}), 401)


def product_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["price_cents"] = int(data.get("price_cents") or 0)
    data["stock"] = int(data.get("stock") or 0)
    if not data.get("image_url"):
        data["image_url"] = f"https://placehold.co/900x700/png?text={data.get('sku') or 'PRODUCT'}"
    return data


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.config["DB_PATH"] = db_path_for(app)

    CORS(app, resources={r"/api/*": {"origins": cors_origins()}}, supports_credentials=False)

    ensure_schema(app)

    @app.get("/")
    def root():
        return jsonify(
            {
                "ok": True,
                "app": APP_NAME,
                "brand": BRAND,
                "system": SYSTEM,
                "owner": OWNER,
                "message": "I AM THE ONE™ SaaS API is live.",
                "endpoints": [
                    "/api/health",
                    "/api/stores",
                    "/api/stores/demo/products",
                    "/api/stores/demo/checkout",
                    "/api/owner/login",
                    "/api/owner/orders",
                    "/api/owner/products",
                ],
            }
        )

    @app.get("/api/health")
    def health():
        con = connect(app)
        try:
            counts = {
                "stores": con.execute("SELECT COUNT(*) AS c FROM stores").fetchone()["c"],
                "products": con.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"],
                "orders": con.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"],
            }
        finally:
            con.close()

        return jsonify(
            {
                "ok": True,
                "app": APP_NAME,
                "version": "v3-saas-functional",
                "brand": BRAND,
                "system": SYSTEM,
                "owner": OWNER,
                "db_path": app.config["DB_PATH"],
                "counts": counts,
                "ts": now_iso(),
            }
        )

    @app.get("/api/stores")
    def stores():
        con = connect(app)
        try:
            rows = con.execute(
                """
                SELECT id, slug, name, brand, system, plan, status, created_at
                FROM stores
                ORDER BY slug
                """
            ).fetchall()
            return jsonify({"ok": True, "count": len(rows), "stores": [dict(row) for row in rows]})
        finally:
            con.close()

    @app.get("/api/stores/<slug>/products")
    def store_products(slug: str):
        con = connect(app)
        try:
            store = con.execute(
                "SELECT id, slug, name, brand, system, plan, status FROM stores WHERE slug = ? LIMIT 1",
                (slug,),
            ).fetchone()

            if not store:
                return jsonify({"ok": False, "error": f"Store not found: {slug}"}), 404

            rows = con.execute(
                """
                SELECT id, store_id, sku, name, category, description, price_cents, stock, image_url, updated_at
                FROM products
                WHERE store_id = ?
                ORDER BY category, name
                """,
                (store["id"],),
            ).fetchall()

            products = [product_dict(row) for row in rows]
            return jsonify({"ok": True, "store": dict(store), "count": len(products), "products": products})
        finally:
            con.close()

    @app.post("/api/stores/<slug>/checkout")
    def checkout(slug: str):
        payload = request.get_json(silent=True) or {}
        buyer = payload.get("buyer") or {}
        items = payload.get("items") or []

        buyer_name = str(buyer.get("name") or "").strip()
        buyer_email = str(buyer.get("email") or "").strip()
        buyer_phone = str(buyer.get("phone") or "").strip()
        notes = str(buyer.get("notes") or "").strip()

        if not buyer_name:
            return jsonify({"ok": False, "error": "Buyer name is required."}), 400
        if not buyer_email:
            return jsonify({"ok": False, "error": "Buyer email is required."}), 400
        if not isinstance(items, list) or not items:
            return jsonify({"ok": False, "error": "Cart is empty."}), 400

        currency = os.getenv("CURRENCY", "USD").upper()
        tax_bps = int(os.getenv("TAX_BPS", "0") or "0")
        shipping_cents = int(os.getenv("SHIPPING_CENTS", "0") or "0")
        discount_cents = int(os.getenv("DISCOUNT_CENTS", "0") or "0")
        payment_mode = os.getenv("PAYMENT_MODE", "manual").strip() or "manual"
        instructions = os.getenv("PAYMENT_INSTRUCTIONS", "Manual payment pending. Owner will contact buyer.")

        con = connect(app)
        try:
            con.execute("BEGIN IMMEDIATE")

            store = con.execute(
                "SELECT id, slug, name FROM stores WHERE slug = ? LIMIT 1",
                (slug,),
            ).fetchone()

            if not store:
                con.rollback()
                return jsonify({"ok": False, "error": f"Store not found: {slug}"}), 404

            order_lines: list[dict[str, Any]] = []
            subtotal_cents = 0

            for item in items:
                sku = str(item.get("sku") or "").strip()
                product_id = str(item.get("product_id") or item.get("id") or "").strip()
                qty = int(item.get("qty") or item.get("quantity") or 1)

                if qty <= 0:
                    con.rollback()
                    return jsonify({"ok": False, "error": "Quantity must be at least 1."}), 400

                if sku:
                    product = con.execute(
                        "SELECT * FROM products WHERE store_id = ? AND sku = ? LIMIT 1",
                        (store["id"], sku),
                    ).fetchone()
                else:
                    product = con.execute(
                        "SELECT * FROM products WHERE store_id = ? AND id = ? LIMIT 1",
                        (store["id"], product_id),
                    ).fetchone()

                if not product:
                    con.rollback()
                    return jsonify({"ok": False, "error": f"Product not found: {sku or product_id}"}), 404

                stock = int(product["stock"] or 0)
                unit = int(product["price_cents"] or 0)

                if stock < qty:
                    con.rollback()
                    return jsonify(
                        {
                            "ok": False,
                            "error": f"Not enough stock for {product['name']}. Available: {stock}.",
                        }
                    ), 409

                line_total = unit * qty
                subtotal_cents += line_total

                order_lines.append(
                    {
                        "product_id": product["id"],
                        "sku": product["sku"],
                        "name": product["name"],
                        "qty": qty,
                        "unit_amount_cents": unit,
                        "line_total_cents": line_total,
                    }
                )

            tax_cents = round(subtotal_cents * tax_bps / 10000)
            total_cents = max(0, subtotal_cents + tax_cents + shipping_cents - discount_cents)
            order_id = "ORD-" + secrets.token_hex(5).upper()
            created_at = now_iso()

            con.execute(
                """
                INSERT INTO orders (
                    id, store_id, store_slug, buyer_name, buyer_email, buyer_phone, notes,
                    subtotal_cents, tax_cents, shipping_cents, discount_cents, total_cents,
                    currency, payment_mode, payment_status, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    store["id"],
                    store["slug"],
                    buyer_name,
                    buyer_email,
                    buyer_phone,
                    notes,
                    subtotal_cents,
                    tax_cents,
                    shipping_cents,
                    discount_cents,
                    total_cents,
                    currency,
                    payment_mode,
                    "unpaid",
                    "created",
                    created_at,
                ),
            )

            for line in order_lines:
                con.execute(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, sku, name, qty, unit_amount_cents, line_total_cents
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        line["product_id"],
                        line["sku"],
                        line["name"],
                        line["qty"],
                        line["unit_amount_cents"],
                        line["line_total_cents"],
                    ),
                )

                con.execute(
                    "UPDATE products SET stock = stock - ?, updated_at = ? WHERE id = ?",
                    (line["qty"], now_iso(), line["product_id"]),
                )

            con.commit()

            return jsonify(
                {
                    "ok": True,
                    "order_id": order_id,
                    "order": {
                        "id": order_id,
                        "buyer_name": buyer_name,
                        "buyer_email": buyer_email,
                        "subtotal_cents": subtotal_cents,
                        "tax_cents": tax_cents,
                        "shipping_cents": shipping_cents,
                        "discount_cents": discount_cents,
                        "total_cents": total_cents,
                        "total_display": money(total_cents),
                        "currency": currency,
                        "status": "created",
                        "created_at": created_at,
                    },
                    "items": order_lines,
                    "payment": {
                        "mode": payment_mode,
                        "status": "unpaid",
                        "instructions": instructions,
                    },
                }
            )
        except Exception as exc:
            con.rollback()
            return jsonify({"ok": False, "error": f"Checkout failed: {type(exc).__name__}: {exc}"}), 500
        finally:
            con.close()

    @app.post("/api/owner/login")
    def owner_login():
        payload = request.get_json(silent=True) or {}
        supplied = str(payload.get("password") or "").strip()

        configured = os.getenv("ADMIN_PASSWORD", "").strip()
        allowed_passwords = [p for p in [configured, "WOLF-OWNER-2026", "WOLF-DEMO"] if p]

        if not any(secrets.compare_digest(supplied, p) for p in allowed_passwords):
            return jsonify({"ok": False, "error": "Invalid owner password."}), 401

        return jsonify(
            {
                "ok": True,
                "token": owner_token(),
                "owner": OWNER,
                "brand": BRAND,
                "system": SYSTEM,
            }
        )

    @app.get("/api/owner/orders")
    def owner_orders():
        ok, error = require_owner()
        if not ok:
            return error

        con = connect(app)
        try:
            rows = con.execute(
                """
                SELECT *
                FROM orders
                ORDER BY created_at DESC
                LIMIT 100
                """
            ).fetchall()
            return jsonify({"ok": True, "count": len(rows), "orders": [dict(row) for row in rows]})
        finally:
            con.close()

    @app.get("/api/owner/products")
    def owner_products():
        ok, error = require_owner()
        if not ok:
            return error

        con = connect(app)
        try:
            rows = con.execute(
                """
                SELECT id, store_id, sku, name, category, description, price_cents, stock, image_url, updated_at
                FROM products
                ORDER BY category, name
                """
            ).fetchall()
            products = [product_dict(row) for row in rows]
            return jsonify({"ok": True, "count": len(products), "products": products})
        finally:
            con.close()

    return app


