# Copyright Â© 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.db import connect, new_id, now_iso, row_to_dict, rows_to_dicts

checkout_bp = Blueprint("checkout", __name__, url_prefix="/api")


def _qty(value) -> int:
    try:
        qty = int(value)
    except Exception:
        qty = 0
    return max(0, qty)


@checkout_bp.post("/stores/<slug>/checkout")
def create_checkout(slug: str):
    data = request.get_json(silent=True) or {}

    buyer = data.get("buyer") or {}
    items = data.get("items") or []

    buyer_name = str(buyer.get("name") or data.get("buyer_name") or "").strip()
    buyer_email = str(buyer.get("email") or data.get("buyer_email") or "").strip()
    buyer_phone = str(buyer.get("phone") or data.get("buyer_phone") or "").strip()
    notes = str(buyer.get("notes") or data.get("notes") or "").strip()

    if not buyer_name or not buyer_email:
        return jsonify({"ok": False, "error": "BUYER_NAME_AND_EMAIL_REQUIRED"}), 400

    if not isinstance(items, list) or not items:
        return jsonify({"ok": False, "error": "CART_ITEMS_REQUIRED"}), 400

    con = connect()

    try:
        con.execute("BEGIN IMMEDIATE")

        store = con.execute("SELECT * FROM stores WHERE slug = ?", (slug,)).fetchone()
        if not store:
            con.rollback()
            return jsonify({"ok": False, "error": "STORE_NOT_FOUND"}), 404

        order_id = new_id("ord")
        created = now_iso()
        subtotal = 0
        order_items = []

        for item in items:
            product_id = str(item.get("product_id") or item.get("id") or "").strip()
            sku = str(item.get("sku") or "").strip().upper()
            qty = _qty(item.get("qty") or item.get("quantity") or 1)

            if qty <= 0:
                con.rollback()
                return jsonify({"ok": False, "error": "INVALID_QTY"}), 400

            if product_id:
                product = con.execute(
                    """
                    SELECT * FROM products
                    WHERE store_slug = ?
                    AND id = ?
                    AND is_active = 1
                    """,
                    (slug, product_id),
                ).fetchone()
            else:
                product = con.execute(
                    """
                    SELECT * FROM products
                    WHERE store_slug = ?
                    AND sku = ?
                    AND is_active = 1
                    """,
                    (slug, sku),
                ).fetchone()

            if not product:
                con.rollback()
                return jsonify({"ok": False, "error": "PRODUCT_NOT_FOUND", "sku": sku, "product_id": product_id}), 404

            stock = int(product["stock"])
            if stock < qty:
                con.rollback()
                return (
                    jsonify(
                        {
                            "ok": False,
                            "error": "INSUFFICIENT_STOCK",
                            "product": row_to_dict(product),
                            "requested_qty": qty,
                            "available_stock": stock,
                        }
                    ),
                    409,
                )

            unit_amount = int(product["price_cents"])
            line_total = unit_amount * qty
            subtotal += line_total

            order_item_id = new_id("item")
            order_items.append(
                {
                    "id": order_item_id,
                    "order_id": order_id,
                    "product_id": product["id"],
                    "sku": product["sku"],
                    "name": product["name"],
                    "qty": qty,
                    "unit_amount_cents": unit_amount,
                    "line_total_cents": line_total,
                }
            )

            con.execute(
                """
                UPDATE products
                SET stock = stock - ?, updated_at = ?
                WHERE id = ?
                """,
                (qty, created, product["id"]),
            )

        tax_bps = int(current_app.config["TAX_BPS"])
        shipping_cents = int(current_app.config["SHIPPING_CENTS"])
        tax_cents = round(subtotal * tax_bps / 10000)
        total_cents = subtotal + tax_cents + shipping_cents

        con.execute(
            """
            INSERT INTO orders
            (id, store_slug, buyer_name, buyer_email, buyer_phone, notes, status, payment_status,
             subtotal_cents, tax_cents, shipping_cents, total_cents, currency, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'new', 'unpaid', ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                slug,
                buyer_name,
                buyer_email,
                buyer_phone,
                notes,
                subtotal,
                tax_cents,
                shipping_cents,
                total_cents,
                current_app.config["CURRENCY"],
                created,
            ),
        )

        for line in order_items:
            con.execute(
                """
                INSERT INTO order_items
                (id, order_id, product_id, sku, name, qty, unit_amount_cents, line_total_cents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    line["id"],
                    line["order_id"],
                    line["product_id"],
                    line["sku"],
                    line["name"],
                    line["qty"],
                    line["unit_amount_cents"],
                    line["line_total_cents"],
                ),
            )

        con.commit()

        order = con.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        updated_products = con.execute(
            """
            SELECT * FROM products
            WHERE store_slug = ?
            AND is_active = 1
            ORDER BY created_at ASC
            """,
            (slug,),
        ).fetchall()

    except Exception as exc:
        con.rollback()
        return jsonify({"ok": False, "error": "CHECKOUT_FAILED", "message": str(exc)}), 500
    finally:
        con.close()

    return (
        jsonify(
            {
                "ok": True,
                "order": row_to_dict(order),
                "items": order_items,
                "updated_products": rows_to_dicts(updated_products),
                "payment": {
                    "mode": "manual",
                    "status": "unpaid",
                    "message": "Order created. Manual payment wiring can be added next.",
                },
            }
        ),
        201,
    )

