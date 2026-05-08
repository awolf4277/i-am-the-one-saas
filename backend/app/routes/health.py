# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health():
    return jsonify(
        ok=True,
        app=current_app.config["APP_BRAND"],
        system=current_app.config["APP_SYSTEM"],
        owner=current_app.config["APP_OWNER"],
        platform="I AM THE ONE SaaS",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )