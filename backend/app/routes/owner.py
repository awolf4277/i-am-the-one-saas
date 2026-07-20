# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import hmac

from flask import Blueprint, current_app, jsonify, request

from app.security import admin_password, owner_token, require_owner

owner_bp = Blueprint("owner", __name__, url_prefix="/api")


@owner_bp.post("/owner/login")
def owner_login():
    data = request.get_json(silent=True) or {}
    supplied_password = str(data.get("password", "")).strip()

    if not supplied_password:
        return jsonify({"ok": False, "error": "PASSWORD_REQUIRED"}), 400

    if not hmac.compare_digest(supplied_password, admin_password()):
        return jsonify({"ok": False, "error": "INVALID_PASSWORD"}), 401

    return jsonify(
        {
            "ok": True,
            "token": owner_token(),
            "owner": current_app.config["APP_OWNER"],
            "brand": current_app.config["APP_BRAND"],
            "system": current_app.config["APP_SYSTEM"],
            "message": "Owner session unlocked.",
        }
    )


@owner_bp.get("/owner/session")
@require_owner
def owner_session():
    return jsonify(
        {
            "ok": True,
            "owner": current_app.config["APP_OWNER"],
            "brand": current_app.config["APP_BRAND"],
            "system": current_app.config["APP_SYSTEM"],
        }
    )

