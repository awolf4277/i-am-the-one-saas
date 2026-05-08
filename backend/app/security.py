# Copyright © 2026 Andrew Wolverton. All Rights Reserved.
from __future__ import annotations

import hmac
from functools import wraps
from typing import Callable, TypeVar

from flask import current_app, jsonify, request

F = TypeVar("F", bound=Callable)


def owner_token() -> str:
    return str(current_app.config.get("OWNER_API_TOKEN", "")).strip()


def admin_password() -> str:
    return str(current_app.config.get("ADMIN_PASSWORD", "")).strip()


def verify_owner_request() -> bool:
    expected = owner_token()
    if not expected:
        return False

    auth = request.headers.get("Authorization", "").strip()
    supplied = ""

    if auth.lower().startswith("bearer "):
        supplied = auth.split(" ", 1)[1].strip()

    if not supplied:
        supplied = request.headers.get("X-Owner-Token", "").strip()

    return bool(supplied) and hmac.compare_digest(supplied, expected)


def require_owner(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not verify_owner_request():
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "OWNER_AUTH_REQUIRED",
                        "message": "Owner API token required.",
                    }
                ),
                401,
            )

        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]