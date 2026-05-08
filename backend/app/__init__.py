# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from .routes.health import health_bp
from .routes.stores import stores_bp


def _cors_origins() -> str | list[str]:
    raw = os.getenv("CORS_ORIGINS", "*").strip()
    if not raw or raw == "*":
        return "*"
    return [item.strip() for item in raw.split(",") if item.strip()]


def create_app() -> Flask:
    app = Flask(__name__)

    base_dir = Path(__file__).resolve().parent

    app.config["JSON_SORT_KEYS"] = False
    app.config["APP_OWNER"] = os.getenv("APP_OWNER", "Andrew Wolverton")
    app.config["APP_BRAND"] = os.getenv("APP_BRAND", "I AM THE ONE™")
    app.config["APP_SYSTEM"] = os.getenv("APP_SYSTEM", "WOLF OS™")
    app.config["DB_PATH"] = os.getenv(
        "DB_PATH",
        str(base_dir / "db" / "i_am_the_one_saas.sqlite3"),
    )
    app.config["MEDIA_SLOTS"] = int(os.getenv("MEDIA_SLOTS", "25"))

    CORS(app, resources={r"/api/*": {"origins": _cors_origins()}})

    app.register_blueprint(health_bp)
    app.register_blueprint(stores_bp)

    return app