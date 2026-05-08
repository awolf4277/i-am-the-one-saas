# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

from flask import jsonify

from app import create_app

app = create_app()


@app.get("/")
def root():
    return jsonify(
        ok=True,
        app="I AM THE ONE™ SaaS API",
        system="WOLF OS™",
        message="Use /api/health, /api/stores, or /api/stores/demo/products.",
    )