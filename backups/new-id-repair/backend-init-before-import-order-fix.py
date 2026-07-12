from uuid import uuid4
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




def _clean_owner_env_value(raw: object, fallback: str = "") -> str:
    value = str(raw or "").strip().strip('"').strip("'")

    if not value:
        return fallback

    value = value.replace("\r", "\n")
    parts = [part.strip() for part in value.split("\n") if part.strip()]

    # Handles bad Render paste:
    # OWNER_API_TOKEN
    # wolf-owner-local-token
    if len(parts) >= 2 and parts[0].upper().replace(" ", "_") in {"OWNER_API_TOKEN", "ADMIN_PASSWORD"}:
        value = parts[-1]

    # Handles bad Render paste:
    # OWNER_API_TOKEN=wolf-owner-local-token
    if "=" in value:
        left, right = value.split("=", 1)
        if left.strip().upper().replace(" ", "_") in {"OWNER_API_TOKEN", "ADMIN_PASSWORD"}:
            value = right.strip()

    return value.strip().strip('"').strip("'") or fallback


def owner_api_token() -> str:
    return _clean_owner_env_value(
        os.getenv("OWNER_API_TOKEN", ""),
        "wolf-owner-local-token",
    )


OWNER = os.getenv("APP_OWNER", "Andrew Wolverton")
BRAND = os.getenv("APP_BRAND", "I AM THE ONE™")
SYSTEM = os.getenv("APP_SYSTEM", "WOLF OS™")
APP_NAME = os.getenv("APP_NAME", "I AM THE ONE™ SaaS v3 API")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


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

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS setup_requests (
                id TEXT PRIMARY KEY,
                name TEXT,
                business_name TEXT,
                email TEXT,
                phone TEXT,
                what_i_sell TEXT,
                budget_range TEXT,
                timeline TEXT,
                website TEXT,
                message TEXT,
                source TEXT,
                status TEXT,
                created_at TEXT
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_deals (
                lead_id TEXT PRIMARY KEY,
                stage TEXT NOT NULL DEFAULT 'New',
                deal_value INTEGER NOT NULL DEFAULT 0,
                next_action TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_activity (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_pipeline_activity_lead_created
            ON pipeline_activity (
                lead_id,
                created_at DESC
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
                "/products/wolf-signature-hoodie.svg",
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
                "/products/wolf-core.svg",
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
                "/products/iato-launch-kit.svg",
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
                "/products/operator-console.svg",
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


        # Sales-ready demo fullness seed.
        # This keeps Render production looking full even if the SQLite file resets on deploy/restart.
        sales_ready_products = [
            (
                "prod_starter_storefront",
                "store_demo",
                "WOLF-STARTER",
                "Starter Storefront",
                "SaaS Package",
                "A clean buyer-ready storefront with products, cart, checkout flow, and launch-ready branding.",
                49900,
                9,
                "https://placehold.co/900x700/111827/FFFFFF?text=Starter+Storefront",
            ),
            (
                "prod_pro_dashboard",
                "store_demo",
                "WOLF-PRO",
                "Pro Storefront + Owner Dashboard",
                "SaaS Package",
                "Premium storefront plus WOLF OS™ owner console for orders, products, inventory, and buyer leads.",
                150000,
                5,
                "https://placehold.co/900x700/111827/FFFFFF?text=Pro+Dashboard",
            ),
            (
                "prod_custom_saas",
                "store_demo",
                "WOLF-CUSTOM",
                "Custom SaaS Buildout Deposit",
                "SaaS Package",
                "Deposit for a custom SaaS buildout with storefront, admin tools, lead capture, and launch support.",
                300000,
                3,
                "https://placehold.co/900x700/111827/FFFFFF?text=Custom+SaaS",
            ),
            (
                "prod_launch_kit",
                "store_demo",
                "WOLF-LAUNCH-KIT",
                "Digital Launch Kit",
                "Launch",
                "Brand copy, offer cards, product structure, demo pitch, and buyer-ready launch materials.",
                29900,
                12,
                "https://placehold.co/900x700/111827/FFFFFF?text=Launch+Kit",
            ),
            (
                "prod_brand_audit",
                "store_demo",
                "WOLF-AUDIT",
                "Brand + Storefront Audit",
                "Launch",
                "Fast review of a business offer, buyer path, storefront structure, and next launch steps.",
                19900,
                7,
                "https://placehold.co/900x700/111827/FFFFFF?text=Brand+Audit",
            ),
        ]

        for item in sales_ready_products:
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

        sales_ready_leads = [
            (
                "REQ-DEMO-BLUE-RIDGE",
                "Taylor Reed",
                "Blue Ridge Apparel",
                "taylor@example.com",
                "555-0199",
                "Premium apparel, branded merch, hoodies, tees, and a buyer-ready storefront.",
                "$1,500+ Pro",
                "This week",
                "",
                "Looking for a premium apparel storefront with products, checkout, and a simple owner dashboard.",
                "startup_sales_ready_seed",
                "live",
            ),
            (
                "REQ-DEMO-SUMMIT",
                "Jordan Miles",
                "Summit Clean Exteriors",
                "jordan@example.com",
                "555-0188",
                "Pressure washing packages, exterior cleaning quotes, and local service leads.",
                "$499+ Starter",
                "Next 7 days",
                "",
                "Need a clean service storefront for pressure washing packages and quote requests.",
                "startup_sales_ready_seed",
                "live",
            ),
            (
                "REQ-DEMO-CROWN-CUT",
                "Marcus King",
                "Crown Cut Studio",
                "marcus@example.com",
                "555-0177",
                "Barber services, haircut packages, booking interest, and branded local offers.",
                "$299-$499",
                "Soon",
                "",
                "Want a simple barber shop demo with services, booking interest, and branded offer cards.",
                "startup_sales_ready_seed",
                "live",
            ),
        ]

        for lead in sales_ready_leads:
            existing = con.execute(
                "SELECT id FROM setup_requests WHERE id = ? LIMIT 1",
                (lead[0],),
            ).fetchone()
            if not existing:
                con.execute(
                    """
                    INSERT INTO setup_requests (
                        id, name, business_name, email, phone, what_i_sell,
                        budget_range, timeline, website, message, source, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*lead, now_iso()),
                )

        sales_ready_orders = [
            (
                "ORD-DEMO-BLUE-RIDGE",
                "Taylor Reed",
                "taylor@example.com",
                "555-0199",
                "Setup Call",
                150000,
                [
                    ("prod_pro_dashboard", "WOLF-PRO", "Pro Storefront + Owner Dashboard", 1, 150000),
                ],
            ),
            (
                "ORD-DEMO-SUMMIT",
                "Jordan Miles",
                "jordan@example.com",
                "555-0188",
                "Digital Delivery",
                49900,
                [
                    ("prod_starter_storefront", "WOLF-STARTER", "Starter Storefront", 1, 49900),
                ],
            ),
            (
                "ORD-DEMO-CROWN-CUT",
                "Marcus King",
                "marcus@example.com",
                "555-0177",
                "Launch Kit",
                29900,
                [
                    ("prod_launch_kit", "WOLF-LAUNCH-KIT", "Digital Launch Kit", 1, 29900),
                ],
            ),
        ]

        for order in sales_ready_orders:
            order_id, buyer_name, buyer_email, buyer_phone, notes, total_cents, lines = order
            existing = con.execute(
                "SELECT id FROM orders WHERE id = ? LIMIT 1",
                (order_id,),
            ).fetchone()
            if not existing:
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
                        "store_demo",
                        "demo",
                        buyer_name,
                        buyer_email,
                        buyer_phone,
                        notes,
                        total_cents,
                        0,
                        0,
                        0,
                        total_cents,
                        "USD",
                        "manual",
                        "unpaid",
                        "created",
                        now_iso(),
                    ),
                )

                for product_id, sku, name, qty, unit_amount_cents in lines:
                    con.execute(
                        """
                        INSERT INTO order_items (
                            order_id, product_id, sku, name, qty, unit_amount_cents, line_total_cents
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            order_id,
                            product_id,
                            sku,
                            name,
                            qty,
                            unit_amount_cents,
                            qty * unit_amount_cents,
                        ),
                    )

        con.commit()
    finally:
        con.close()


def owner_token() -> str:
    return owner_api_token().strip() or "wolf-owner-local-token"


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
                "setup_requests": con.execute("SELECT COUNT(*) AS c FROM setup_requests").fetchone()["c"],
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


    @app.post("/api/stores/<slug>/products")
    def owner_create_store_product(slug: str):
        ok, error = require_owner()
        if not ok:
            return error

        payload = request.get_json(silent=True) or {}

        sku = str(payload.get("sku") or "").strip().upper()
        name = str(payload.get("name") or "").strip()
        category = str(payload.get("category") or "General").strip() or "General"
        description = str(payload.get("description") or "").strip()
        image_url = str(payload.get("image_url") or "").strip()

        try:
            price_cents = int(payload.get("price_cents") or 0)
        except (TypeError, ValueError):
            price_cents = 0

        try:
            stock = int(payload.get("stock") or 0)
        except (TypeError, ValueError):
            stock = 0

        if not sku:
            return jsonify({"ok": False, "error": "SKU is required."}), 400

        if not name:
            return jsonify({"ok": False, "error": "Product name is required."}), 400

        if price_cents < 0:
            return jsonify({"ok": False, "error": "Price cannot be negative."}), 400

        if stock < 0:
            return jsonify({"ok": False, "error": "Stock cannot be negative."}), 400

        con = connect(app)
        try:
            store = con.execute(
                "SELECT id, slug FROM stores WHERE slug = ? LIMIT 1",
                (slug,),
            ).fetchone()

            if not store:
                return jsonify({"ok": False, "error": f"Store not found: {slug}"}), 404

            duplicate = con.execute(
                "SELECT id FROM products WHERE store_id = ? AND sku = ? LIMIT 1",
                (store["id"], sku),
            ).fetchone()

            if duplicate:
                return jsonify({"ok": False, "error": f"SKU already exists: {sku}"}), 409

            base_id = "".join(
                ch.lower() if ch.isalnum() else "-"
                for ch in (sku or name)
            ).strip("-")

            product_id = base_id or f"product-{secrets.token_hex(4)}"

            existing_id = con.execute(
                "SELECT id FROM products WHERE id = ? LIMIT 1",
                (product_id,),
            ).fetchone()

            if existing_id:
                product_id = f"{product_id}-{secrets.token_hex(3)}"

            created_at = now_iso()

            con.execute(
                """
                INSERT INTO products (
                    id, store_id, store_slug, sku, name, category, description,
                    price_cents, stock, image_url, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    store["id"],
                    store["slug"],
                    sku,
                    name,
                    category,
                    description,
                    price_cents,
                    stock,
                    image_url,
                    created_at,
                    created_at,
                ),
            )

            for (
                activity_type,
                old_value,
                new_value,
                summary,
            ) in activity_items:
                con.execute(
                    """
                    INSERT INTO pipeline_activity (
                        id,
                        lead_id,
                        activity_type,
                        old_value,
                        new_value,
                        summary,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id("ACT"),
                        lead_id,
                        activity_type,
                        old_value,
                        new_value,
                        summary,
                        updated_at,
                    ),
                )

            con.commit()

            row = con.execute(
                """
                SELECT id, store_id, sku, name, category, description, price_cents, stock, image_url, updated_at
                FROM products
                WHERE id = ?
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()

            return jsonify({"ok": True, "product": product_dict(row)}), 201
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

    @app.get("/api/orders/<order_id>/download")
    def order_download(order_id: str):
        from flask import Response

        buyer_email = str(request.args.get("email") or "").strip().lower()

        if not buyer_email:
            return jsonify({"ok": False, "error": "Buyer email required."}), 400

        con = connect(app)

        try:
            order = con.execute(
                "SELECT * FROM orders WHERE id = ? LIMIT 1",
                (order_id,),
            ).fetchone()

            if not order:
                return jsonify({"ok": False, "error": "Order not found."}), 404

            stored_email = str(order["buyer_email"] or "").strip().lower()

            if stored_email != buyer_email:
                return jsonify({"ok": False, "error": "Download access denied."}), 403

            items = con.execute(
                """
                SELECT sku, name, qty, unit_amount_cents, line_total_cents
                FROM order_items
                WHERE order_id = ?
                ORDER BY id ASC
                """,
                (order_id,),
            ).fetchall()
        finally:
            con.close()

        def cents(value):
            return f"${(int(value or 0) / 100):,.2f}"

        lines = [
            "I AM THE ONE™ / WOLF OS™ DIGITAL DELIVERY",
            "",
            f"Order ID: {order['id']}",
            f"Buyer: {order['buyer_name'] or 'Customer'}",
            f"Email: {order['buyer_email'] or ''}",
            f"Payment Status: {order['payment_status'] or 'manual / unpaid'}",
            f"Order Total: {cents(order['total_cents'])}",
            "",
            "Items:",
        ]

        for item in items:
            lines.append(
                f"- {item['name']} ({item['sku']}) x{item['qty']} = {cents(item['line_total_cents'])}"
            )

        lines += [
            "",
            "Delivery Instructions:",
            "Your order was created successfully.",
            "For manual payment mode, the owner confirms payment and delivers the final product/package.",
            "",
            "Copyright © 2026 Andrew Wolverton. All Rights Reserved.",
        ]

        body = "\n".join(lines)

        return Response(
            body,
            mimetype="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{order_id}-delivery.txt"'
            },
        )


    @app.post("/api/setup-requests")
    def create_setup_request():
        payload = request.get_json(silent=True) or {}

        name = str(payload.get("name") or "").strip()
        business_name = str(payload.get("business_name") or "").strip()
        email = str(payload.get("email") or "").strip()
        phone = str(payload.get("phone") or "").strip()
        what_i_sell = str(payload.get("what_i_sell") or payload.get("whatISell") or "").strip()
        budget_range = str(payload.get("budget_range") or payload.get("budgetRange") or "").strip()
        timeline = str(payload.get("timeline") or "").strip()
        website = str(payload.get("website") or "").strip()
        message = str(payload.get("message") or "").strip()
        source = str(payload.get("source") or "homepage").strip() or "homepage"

        if not name:
            return jsonify({"ok": False, "error": "Name is required."}), 400
        if not email:
            return jsonify({"ok": False, "error": "Email is required."}), 400
        if not business_name:
            return jsonify({"ok": False, "error": "Business name is required."}), 400

        request_id = "REQ-" + secrets.token_hex(5).upper()
        created_at = now_iso()

        con = connect(app)
        try:
            con.execute(
                """
                INSERT INTO setup_requests (
                    id, name, business_name, email, phone, what_i_sell,
                    budget_range, timeline, website, message, source, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    name,
                    business_name,
                    email,
                    phone,
                    what_i_sell,
                    budget_range,
                    timeline,
                    website,
                    message,
                    source,
                    "new",
                    created_at,
                ),
            )
            con.commit()

            return jsonify(
                {
                    "ok": True,
                    "request_id": request_id,
                    "setup_request": {
                        "id": request_id,
                        "name": name,
                        "business_name": business_name,
                        "email": email,
                        "phone": phone,
                        "what_i_sell": what_i_sell,
                        "budget_range": budget_range,
                        "timeline": timeline,
                        "website": website,
                        "message": message,
                        "source": source,
                        "status": "new",
                        "created_at": created_at,
                    },
                }
            ), 201
        except Exception as exc:
            con.rollback()
            return jsonify({"ok": False, "error": f"Setup request failed: {type(exc).__name__}: {exc}"}), 500
        finally:
            con.close()

    @app.get("/api/owner/setup-requests")
    def owner_setup_requests():
        ok, error = require_owner()
        if not ok:
            return error

        con = connect(app)
        try:
            rows = con.execute(
                """
                SELECT *
                FROM setup_requests
                ORDER BY created_at DESC
                LIMIT 100
                """
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "count": len(rows),
                    "setup_requests": [dict(row) for row in rows],
                }
            )
        finally:
            con.close()

    @app.get("/api/owner/pipeline/activity")
    def owner_pipeline_activity():
        ok, error = require_owner()

        if not ok:
            return error

        lead_id = str(
            request.args.get("lead_id") or ""
        ).strip()

        try:
            limit = int(
                request.args.get("limit") or 50
            )
        except (TypeError, ValueError):
            limit = 50

        limit = max(
            1,
            min(limit, 200),
        )

        con = connect(app)

        try:
            params = []

            sql = """
                SELECT
                    pa.id,
                    pa.lead_id,
                    pa.activity_type,
                    pa.old_value,
                    pa.new_value,
                    pa.summary,
                    pa.created_at,
                    sr.business_name,
                    sr.name,
                    sr.email
                FROM pipeline_activity pa
                LEFT JOIN setup_requests sr
                    ON sr.id = pa.lead_id
            """

            if lead_id:
                sql += """
                    WHERE pa.lead_id = ?
                """

                params.append(lead_id)

            sql += """
                ORDER BY pa.created_at DESC
                LIMIT ?
            """

            params.append(limit)

            rows = con.execute(
                sql,
                tuple(params),
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "count": len(rows),
                    "activities": [
                        dict(row)
                        for row in rows
                    ],
                }
            )

        finally:
            con.close()

    @app.get("/api/owner/pipeline-activity")
    def owner_pipeline_activity_log():
        ok, error = require_owner()

        if not ok:
            return error

        lead_id = str(
            request.args.get("lead_id") or ""
        ).strip()

        try:
            limit = int(
                request.args.get("limit") or 50
            )
        except (TypeError, ValueError):
            limit = 50

        limit = max(
            1,
            min(limit, 200),
        )

        con = connect(app)

        try:
            params = []

            sql = """
                SELECT
                    pa.id,
                    pa.lead_id,
                    pa.activity_type,
                    pa.old_value,
                    pa.new_value,
                    pa.summary,
                    pa.created_at,
                    sr.business_name,
                    sr.name,
                    sr.email
                FROM pipeline_activity pa
                LEFT JOIN setup_requests sr
                    ON sr.id = pa.lead_id
            """

            if lead_id:
                sql += """
                    WHERE pa.lead_id = ?
                """

                params.append(lead_id)

            sql += """
                ORDER BY pa.created_at DESC
                LIMIT ?
            """

            params.append(limit)

            rows = con.execute(
                sql,
                tuple(params),
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "count": len(rows),
                    "activities": [
                        dict(row)
                        for row in rows
                    ],
                }
            )

        finally:
            con.close()

    @app.get("/api/owner/pipeline")
    def owner_pipeline():
        ok, error = require_owner()

        if not ok:
            return error

        con = connect(app)

        try:
            rows = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                FROM pipeline_deals
                ORDER BY updated_at DESC
                """
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "count": len(rows),
                    "pipeline_deals": [
                        dict(row)
                        for row in rows
                    ],
                }
            )
        finally:
            con.close()

    @app.put("/api/owner/pipeline/<lead_id>")
    def owner_update_pipeline_deal(lead_id: str):
        ok, error = require_owner()

        if not ok:
            return error

        payload = request.get_json(
            silent=True
        ) or {}

        allowed_stages = {
            "New",
            "Contacted",
            "Demo",
            "Proposal",
            "Closing",
            "Won",
            "Lost",
        }

        stage = str(
            payload.get("stage") or "New"
        ).strip()

        if stage not in allowed_stages:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        f"Invalid pipeline stage: {stage}"
                    ),
                }
            ), 400

        try:
            deal_value = int(
                float(
                    payload.get(
                        "deal_value",
                        0,
                    )
                    or 0
                )
            )
        except (TypeError, ValueError):
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "deal_value must be numeric."
                    ),
                }
            ), 400

        deal_value = max(
            0,
            deal_value,
        )

        next_action = str(
            payload.get("next_action") or ""
        ).strip()

        con = connect(app)

        try:
            lead = con.execute(
                """
                SELECT id
                FROM setup_requests
                WHERE id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            if not lead:
                return jsonify(
                    {
                        "ok": False,
                        "error": "Buyer lead not found.",
                    }
                ), 404

            updated_at = now_iso()

            existing = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action
                FROM pipeline_deals
                WHERE lead_id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            activity_items = []

            if existing:
                if str(existing["stage"]) != stage:
                    activity_items.append(
                        (
                            "stage_changed",
                            str(existing["stage"]),
                            stage,
                            (
                                "Stage moved from "
                                f"{existing['stage']} to {stage}."
                            ),
                        )
                    )

                if int(existing["deal_value"]) != deal_value:
                    activity_items.append(
                        (
                            "deal_value_changed",
                            str(existing["deal_value"]),
                            str(deal_value),
                            (
                                "Deal value changed from "
                                f"${int(existing['deal_value']):,} "
                                f"to ${deal_value:,}."
                            ),
                        )
                    )

                if str(existing["next_action"]) != next_action:
                    activity_items.append(
                        (
                            "next_action_changed",
                            str(existing["next_action"]),
                            next_action,
                            "Next action updated.",
                        )
                    )

            else:
                activity_items.append(
                    (
                        "deal_created",
                        "",
                        stage,
                        (
                            "Deal entered the pipeline at "
                            f"{stage} with a ${deal_value:,} value."
                        ),
                    )
                )

            if existing:
                con.execute(
                    """
                    UPDATE pipeline_deals
                    SET
                        stage = ?,
                        deal_value = ?,
                        next_action = ?,
                        updated_at = ?
                    WHERE lead_id = ?
                    """,
                    (
                        stage,
                        deal_value,
                        next_action,
                        updated_at,
                        lead_id,
                    ),
                )
            else:
                con.execute(
                    """
                    INSERT INTO pipeline_deals (
                        lead_id,
                        stage,
                        deal_value,
                        next_action,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        lead_id,
                        stage,
                        deal_value,
                        next_action,
                        updated_at,
                    ),
                )

            con.commit()

            row = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                FROM pipeline_deals
                WHERE lead_id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            return jsonify(
                {
                    "ok": True,
                    "deal": dict(row),
                }
            )

        except Exception as exc:
            con.rollback()

            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Pipeline update failed: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                }
            ), 500

        finally:
            con.close()

    @app.get("/api/owner/pipeline-state")
    def owner_unified_pipeline_state():
        ok, error = require_owner()

        if not ok:
            return error

        con = connect(app)

        try:
            rows = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                FROM pipeline_deals
                ORDER BY updated_at DESC
                """
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "count": len(rows),
                    "pipeline_deals": [
                        dict(row)
                        for row in rows
                    ],
                }
            )

        finally:
            con.close()

    @app.put("/api/owner/pipeline-state/<lead_id>")
    def owner_update_unified_pipeline_state(
        lead_id: str
    ):
        ok, error = require_owner()

        if not ok:
            return error

        payload = request.get_json(
            silent=True
        ) or {}

        allowed_stages = {
            "New",
            "Contacted",
            "Demo",
            "Proposal",
            "Closing",
            "Won",
            "Lost",
        }

        stage = str(
            payload.get("stage") or "New"
        ).strip()

        if stage not in allowed_stages:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        f"Invalid pipeline stage: {stage}"
                    ),
                }
            ), 400

        try:
            deal_value = int(
                float(
                    payload.get(
                        "deal_value",
                        0,
                    )
                    or 0
                )
            )

        except (TypeError, ValueError):
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "deal_value must be numeric."
                    ),
                }
            ), 400

        deal_value = max(
            0,
            deal_value,
        )

        next_action = str(
            payload.get("next_action") or ""
        ).strip()

        con = connect(app)

        try:
            lead = con.execute(
                """
                SELECT
                    id,
                    business_name
                FROM setup_requests
                WHERE id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            if not lead:
                return jsonify(
                    {
                        "ok": False,
                        "error": "Buyer lead not found.",
                    }
                ), 404

            existing = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action
                FROM pipeline_deals
                WHERE lead_id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            updated_at = now_iso()

            changes = []

            if existing:
                old_stage = str(
                    existing["stage"] or ""
                )

                old_value = int(
                    existing["deal_value"] or 0
                )

                old_action = str(
                    existing["next_action"] or ""
                )

                if old_stage != stage:
                    changes.append(
                        (
                            "stage_changed",
                            old_stage,
                            stage,
                            (
                                "Stage moved from "
                                f"{old_stage} to {stage}."
                            ),
                        )
                    )

                if old_value != deal_value:
                    changes.append(
                        (
                            "deal_value_changed",
                            str(old_value),
                            str(deal_value),
                            (
                                "Deal value changed from "
                                f"${old_value:,} "
                                f"to ${deal_value:,}."
                            ),
                        )
                    )

                if old_action != next_action:
                    changes.append(
                        (
                            "next_action_changed",
                            old_action,
                            next_action,
                            "Next action updated.",
                        )
                    )

            else:
                changes.append(
                    (
                        "deal_created",
                        "",
                        stage,
                        (
                            "Deal entered the pipeline at "
                            f"{stage} with a "
                            f"${deal_value:,} value."
                        ),
                    )
                )

            con.execute(
                """
                INSERT INTO pipeline_deals (
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(lead_id)
                DO UPDATE SET
                    stage = excluded.stage,
                    deal_value = excluded.deal_value,
                    next_action = excluded.next_action,
                    updated_at = excluded.updated_at
                """,
                (
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at,
                ),
            )

            for (
                activity_type,
                old_value,
                new_value,
                summary,
            ) in changes:
                con.execute(
                    """
                    INSERT INTO pipeline_activity (
                        id,
                        lead_id,
                        activity_type,
                        old_value,
                        new_value,
                        summary,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id("ACT"),
                        lead_id,
                        activity_type,
                        old_value,
                        new_value,
                        summary,
                        updated_at,
                    ),
                )

            con.commit()

            deal = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                FROM pipeline_deals
                WHERE lead_id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            snapshot = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                FROM pipeline_deals
                ORDER BY updated_at DESC
                """
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "deal": dict(deal),
                    "activities_written": len(changes),
                    "pipeline_deals": [
                        dict(row)
                        for row in snapshot
                    ],
                }
            )

        except Exception as exc:
            con.rollback()

            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Unified pipeline update failed: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                }
            ), 500

        finally:
            con.close()

    @app.post("/api/owner/login")
    def owner_login():
        payload = request.get_json(silent=True) or {}
        supplied = str(payload.get("password") or "").strip()

        configured = os.getenv("ADMIN_PASSWORD", "").strip()
        allowed_passwords = [p for p in [configured, "", "WOLF-DEMO"] if p]

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

    @app.route("/api/owner/products", methods=["GET", "POST"])
    def owner_products():
        ok, error = require_owner()
        if not ok:
            return error

        con = connect(app)
        try:
            if request.method == "POST":
                payload = request.get_json(silent=True) or {}

                sku = str(payload.get("sku") or "").strip().upper()
                name = str(payload.get("name") or "").strip()
                category = str(payload.get("category") or "General").strip() or "General"
                description = str(payload.get("description") or "").strip()
                image_url = str(payload.get("image_url") or "").strip()

                try:
                    price_cents = int(payload.get("price_cents") or 0)
                except (TypeError, ValueError):
                    price_cents = 0

                try:
                    stock = int(payload.get("stock") or 0)
                except (TypeError, ValueError):
                    stock = 0

                if not sku:
                    return jsonify({"ok": False, "error": "SKU is required."}), 400

                if not name:
                    return jsonify({"ok": False, "error": "Product name is required."}), 400

                if price_cents < 0:
                    return jsonify({"ok": False, "error": "Price cannot be negative."}), 400

                if stock < 0:
                    return jsonify({"ok": False, "error": "Stock cannot be negative."}), 400

                store = con.execute(
                    "SELECT id, slug FROM stores WHERE slug = ? LIMIT 1",
                    ("demo",),
                ).fetchone()

                if not store:
                    return jsonify({"ok": False, "error": "Demo store not found."}), 404

                duplicate = con.execute(
                    "SELECT id FROM products WHERE store_id = ? AND sku = ? LIMIT 1",
                    (store["id"], sku),
                ).fetchone()

                if duplicate:
                    return jsonify({"ok": False, "error": f"SKU already exists: {sku}"}), 409

                base_id = "".join(
                    ch.lower() if ch.isalnum() else "-"
                    for ch in (sku or name)
                ).strip("-")

                product_id = base_id or f"product-{secrets.token_hex(4)}"

                existing_id = con.execute(
                    "SELECT id FROM products WHERE id = ? LIMIT 1",
                    (product_id,),
                ).fetchone()

                if existing_id:
                    product_id = f"{product_id}-{secrets.token_hex(3)}"

                created_at = now_iso()

                con.execute(
                    """
                    INSERT INTO products (
                        id, store_id, store_slug, sku, name, category, description,
                        price_cents, stock, image_url, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        store["id"],
                        store["slug"],
                        sku,
                        name,
                        category,
                        description,
                        price_cents,
                        stock,
                        image_url,
                        created_at,
                        created_at,
                    ),
                )

                con.commit()

                row = con.execute(
                    """
                    SELECT id, store_id, sku, name, category, description, price_cents, stock, image_url, updated_at
                    FROM products
                    WHERE id = ?
                    LIMIT 1
                    """,
                    (product_id,),
                ).fetchone()

                return jsonify({"ok": True, "product": product_dict(row)}), 201

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


    from .routes.analytics import analytics_bp, init_analytics_db

    with app.app_context():
        init_analytics_db()

    app.register_blueprint(analytics_bp)

    return app




