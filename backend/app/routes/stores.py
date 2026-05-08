# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

from flask import Blueprint, jsonify

stores_bp = Blueprint("stores", __name__, url_prefix="/api")


DEMO_STORES = [
    {
        "id": "store_demo",
        "slug": "demo",
        "name": "I AM THE ONE™ Demo Store",
        "brand": "I AM THE ONE™",
        "system": "WOLF OS™",
        "status": "active",
        "plan": "demo",
    }
]


DEMO_PRODUCTS = [
    {
        "id": "wolf-core",
        "store_id": "store_demo",
        "sku": "WOLF-CORE",
        "name": "WOLF OS™ Core",
        "category": "Software",
        "description": "Foundational operator system package for modern storefront control.",
        "price_cents": 9900,
        "stock": 25,
        "image_url": "https://placehold.co/900x700/png?text=WOLF+OS+CORE",
    },
    {
        "id": "iato-launch",
        "store_id": "store_demo",
        "sku": "IATO-LAUNCH",
        "name": "I AM THE ONE™ Launch Kit",
        "category": "Launch",
        "description": "Starter package for branded storefront deployment.",
        "price_cents": 29900,
        "stock": 7,
        "image_url": "https://placehold.co/900x700/png?text=I+AM+THE+ONE",
    },
]


def _find_store(slug: str):
    clean_slug = slug.strip().lower()
    for store in DEMO_STORES:
        if store["slug"] == clean_slug:
            return store
    return None


@stores_bp.get("/stores")
def list_stores():
    return jsonify(ok=True, stores=DEMO_STORES, count=len(DEMO_STORES))


@stores_bp.get("/stores/<slug>")
def get_store(slug: str):
    store = _find_store(slug)
    if not store:
        return jsonify(ok=False, error="Store not found"), 404

    return jsonify(ok=True, store=store)


@stores_bp.get("/stores/<slug>/products")
def get_store_products(slug: str):
    store = _find_store(slug)
    if not store:
        return jsonify(ok=False, error="Store not found"), 404

    products = [
        product
        for product in DEMO_PRODUCTS
        if product["store_id"] == store["id"]
    ]

    return jsonify(
        ok=True,
        store=store,
        products=products,
        count=len(products),
    )