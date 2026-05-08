# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import current_app


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12].upper()}"


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(current_app.config["DB_PATH"])
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def init_db() -> None:
    db_file = Path(current_app.config["DB_PATH"])
    db_file.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(db_file))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")

    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS stores (
                id TEXT PRIMARY KEY,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                plan TEXT NOT NULL DEFAULT 'v3',
                currency TEXT NOT NULL DEFAULT 'USD',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                store_slug TEXT NOT NULL,
                sku TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Premium',
                description TEXT NOT NULL DEFAULT '',
                price_cents INTEGER NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,
                image_url TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(store_slug, sku),
                FOREIGN KEY(store_slug) REFERENCES stores(slug) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                store_slug TEXT NOT NULL,
                buyer_name TEXT NOT NULL,
                buyer_email TEXT NOT NULL,
                buyer_phone TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'new',
                payment_status TEXT NOT NULL DEFAULT 'unpaid',
                subtotal_cents INTEGER NOT NULL DEFAULT 0,
                tax_cents INTEGER NOT NULL DEFAULT 0,
                shipping_cents INTEGER NOT NULL DEFAULT 0,
                total_cents INTEGER NOT NULL DEFAULT 0,
                currency TEXT NOT NULL DEFAULT 'USD',
                created_at TEXT NOT NULL,
                FOREIGN KEY(store_slug) REFERENCES stores(slug) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                name TEXT NOT NULL,
                qty INTEGER NOT NULL,
                unit_amount_cents INTEGER NOT NULL,
                line_total_cents INTEGER NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );

            CREATE INDEX IF NOT EXISTS idx_products_store_slug ON products(store_slug);
            CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
            CREATE INDEX IF NOT EXISTS idx_orders_store_slug ON orders(store_slug);
            CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
            """
        )

        seed_if_empty(con)
        con.commit()
    finally:
        con.close()


def seed_if_empty(con: sqlite3.Connection) -> None:
    row = con.execute("SELECT COUNT(*) AS count FROM stores").fetchone()
    if int(row["count"]) > 0:
        return

    owner = current_app.config["APP_OWNER"]
    currency = current_app.config["CURRENCY"]
    created = now_iso()

    stores = [
        {
            "id": new_id("store"),
            "slug": "demo",
            "name": "I AM THE ONE™ Demo Store",
            "owner_name": owner,
            "status": "active",
            "plan": "v3-saas",
            "currency": currency,
        },
        {
            "id": new_id("store"),
            "slug": "main",
            "name": "I AM THE ONE™ Main Store",
            "owner_name": owner,
            "status": "active",
            "plan": "v3-saas",
            "currency": currency,
        },
    ]

    for store in stores:
        con.execute(
            """
            INSERT INTO stores
            (id, slug, name, owner_name, status, plan, currency, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                store["id"],
                store["slug"],
                store["name"],
                store["owner_name"],
                store["status"],
                store["plan"],
                store["currency"],
                created,
                created,
            ),
        )

    seed_products = [
        ("WOLF-001", "Wolf Signature Hoodie", "Apparel", "Premium heavyweight hoodie for the WOLF OS™ storefront.", 9900, 12),
        ("WOLF-002", "I AM THE ONE™ Tee", "Apparel", "Clean branded tee for a luxury commerce demo package.", 4200, 18),
        ("WOLF-003", "Operator Console License", "Software", "Digital owner/operator license package.", 29900, 50),
        ("WOLF-004", "Storefront Setup Package", "Service", "Turnkey store setup for a buyer-owned storefront.", 49900, 20),
        ("WOLF-005", "Premium Product Drop", "Premium", "Limited product card for live checkout testing.", 14900, 9),
        ("WOLF-006", "SaaS Launch Kit", "Software", "Launch-ready SaaS package with owner dashboard direction.", 99900, 5),
        ("WOLF-007", "Brand Buildout Package", "Service", "Custom brand and storefront configuration package.", 129900, 3),
        ("WOLF-008", "Executive Commerce Bundle", "Premium", "High-ticket bundled offer for revenue showcase.", 249900, 2),
    ]

    for slug in ["demo", "main"]:
        for sku, name, category, description, price_cents, stock in seed_products:
            con.execute(
                """
                INSERT INTO products
                (id, store_slug, sku, name, category, description, price_cents, stock, image_url, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    new_id("prod"),
                    slug,
                    sku,
                    name,
                    category,
                    description,
                    price_cents,
                    stock,
                    "",
                    created,
                    created,
                ),
            )