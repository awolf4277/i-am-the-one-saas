# Copyright Â© 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS


def _csv_env(name: str, default: str = "*") -> str | list[str]:
    raw = os.getenv(name, default).strip()
    if not raw or raw == "*":
        return "*"
    return [part.strip() for part in raw.split(",") if part.strip()]


def create_app() -> Flask:
    backend_dir = Path(__file__).resolve().parent.parent
    load_dotenv(backend_dir / ".env")

    app = Flask(__name__)

    app.config["JSON_SORT_KEYS"] = False
    app.config["BACKEND_DIR"] = str(backend_dir)
    app.config["APP_OWNER"] = os.getenv("APP_OWNER", "Andrew Wolverton")
    app.config["APP_BRAND"] = os.getenv("APP_BRAND", "I AM THE ONEâ„¢")
    app.config["APP_SYSTEM"] = os.getenv("APP_SYSTEM", "WOLF OSâ„¢")
    app.config["APP_NAME"] = os.getenv("APP_NAME", "I AM THE ONEâ„¢ SaaS v3 API")

    db_path = os.getenv("DB_PATH", "data/i_am_the_one_saas_v3.sqlite3")
    if not os.path.isabs(db_path):
      db_path = str(backend_dir / db_path)

    app.config["DB_PATH"] = db_path
    app.config["CURRENCY"] = os.getenv("CURRENCY", "USD")
    app.config["TAX_BPS"] = int(os.getenv("TAX_BPS", "0") or "0")
    app.config["SHIPPING_CENTS"] = int(os.getenv("SHIPPING_CENTS", "0") or "0")
    app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "WOLF-DEMO")
    app.config["OWNER_API_TOKEN"] = os.getenv("OWNER_API_TOKEN", "wolf-owner-local-2026")

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": _csv_env("CORS_ORIGINS", "*"),
                "allow_headers": ["Content-Type", "Authorization", "X-Owner-Token"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            }
        },
    )

    from .db import init_db
    from .routes.health import health_bp
    from .routes.stores import stores_bp
    from .routes.products import products_bp
    from .routes.checkout import checkout_bp
    from .routes.orders import orders_bp
    from .routes.owner import owner_bp

    with app.app_context():
        init_db()

    app.register_blueprint(health_bp)
    app.register_blueprint(stores_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(owner_bp)

    @app.get("/")
    def index():
        return jsonify(
            {
                "ok": True,
                "app": app.config["APP_NAME"],
                "brand": app.config["APP_BRAND"],
                "system": app.config["APP_SYSTEM"],
                "owner": app.config["APP_OWNER"],
                "routes": [
                    "/api/health",
                    "/api/stores",
                    "/api/stores/demo/products",
                    "/api/stores/demo/checkout",
                    "/api/owner/login",
                    "/api/owner/orders",
                    "/api/owner/products",
                    "/api/owner/stores",
                ],
            }
        )

    return app

