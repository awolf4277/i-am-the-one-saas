from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import shutil

ROOT = Path(r"X:\i-am-the-one-saas")
BACKEND = ROOT / "backend" / "app" / "__init__.py"
FRONTEND_FILES = [
    ROOT / "frontend" / "src" / "components" / "BuyerPipelineBoard.tsx",
    ROOT / "frontend" / "src" / "components" / "DealActivityTimeline.tsx",
    ROOT / "frontend" / "src" / "components" / "PriorityEngine.tsx",
    ROOT / "frontend" / "src" / "components" / "RevenueCommandCenter.tsx",
    ROOT / "frontend" / "src" / "lib" / "pipelineState.ts",
]

START = '    @app.put("/api/owner/orders/<order_id>/payment-status")'
END = '    @app.route("/api/owner/products", methods=["GET", "POST"])'
MARKER = "PAYMENT_FREEDOM_BACKEND_V1"

ROUTES = '    # PAYMENT_FREEDOM_BACKEND_V1\n    def ensure_payment_freedom_table(con):\n        con.execute(\n            """\n            CREATE TABLE IF NOT EXISTS payment_freedom_records (\n                order_id TEXT PRIMARY KEY,\n                payment_status TEXT NOT NULL DEFAULT \'unpaid\',\n                payment_method TEXT NOT NULL DEFAULT \'manual\',\n                provider TEXT NOT NULL DEFAULT \'owner_directed\',\n                payment_link TEXT NOT NULL DEFAULT \'\',\n                payment_reference TEXT NOT NULL DEFAULT \'\',\n                amount_cents INTEGER NOT NULL DEFAULT 0,\n                note TEXT NOT NULL DEFAULT \'\',\n                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n            )\n            """\n        )\n        con.commit()\n\n    @app.get("/api/owner/payment-freedom")\n    def owner_payment_freedom():\n        ok, error = require_owner()\n\n        if not ok:\n            return error\n\n        con = connect(app)\n\n        try:\n            ensure_payment_freedom_table(con)\n\n            rows = con.execute(\n                """\n                SELECT *\n                FROM payment_freedom_records\n                ORDER BY updated_at DESC\n                LIMIT 200\n                """\n            ).fetchall()\n\n            return jsonify(\n                {\n                    "ok": True,\n                    "count": len(rows),\n                    "payments": [\n                        dict(row)\n                        for row in rows\n                    ],\n                }\n            )\n        finally:\n            con.close()\n\n    @app.put("/api/owner/orders/<order_id>/payment-status")\n    def owner_update_order_payment_status(\n        order_id: str\n    ):\n        ok, error = require_owner()\n\n        if not ok:\n            return error\n\n        payload = request.get_json(\n            silent=True\n        )\n\n        if not isinstance(payload, dict):\n            return jsonify(\n                {\n                    "ok": False,\n                    "error": (\n                        "Request body must "\n                        "be a JSON object."\n                    ),\n                }\n            ), 400\n\n        if "payment_status" not in payload:\n            return jsonify(\n                {\n                    "ok": False,\n                    "error": (\n                        "payment_status is required."\n                    ),\n                }\n            ), 400\n\n        payment_status = str(\n            payload["payment_status"]\n            or ""\n        ).strip().lower()\n\n        allowed_statuses = {\n            "unpaid",\n            "pending",\n            "deposit_due",\n            "deposit_paid",\n            "partially_paid",\n            "paid",\n            "refunded",\n            "cancelled",\n        }\n\n        if payment_status not in allowed_statuses:\n            return jsonify(\n                {\n                    "ok": False,\n                    "error": (\n                        "payment_status must be one of: "\n                        + ", ".join(\n                            sorted(allowed_statuses)\n                        )\n                        + "."\n                    ),\n                }\n            ), 400\n\n        con = connect(app)\n\n        try:\n            ensure_payment_freedom_table(con)\n\n            order = con.execute(\n                """\n                SELECT *\n                FROM orders\n                WHERE id = ?\n                LIMIT 1\n                """,\n                (order_id,),\n            ).fetchone()\n\n            if order is None:\n                return jsonify(\n                    {\n                        "ok": False,\n                        "error": "Order not found.",\n                    }\n                ), 404\n\n            existing = con.execute(\n                """\n                SELECT *\n                FROM payment_freedom_records\n                WHERE order_id = ?\n                LIMIT 1\n                """,\n                (order_id,),\n            ).fetchone()\n\n            existing_data = (\n                dict(existing)\n                if existing is not None\n                else {}\n            )\n\n            def payment_text(\n                key: str,\n                default: str,\n                maximum: int\n            ) -> str:\n                value = str(\n                    payload.get(\n                        key,\n                        existing_data.get(\n                            key,\n                            default\n                        )\n                    )\n                    or ""\n                ).strip()\n\n                if len(value) > maximum:\n                    raise ValueError(\n                        f"{key} must be "\n                        f"{maximum} characters or fewer."\n                    )\n\n                return value\n\n            try:\n                payment_method = payment_text(\n                    "payment_method",\n                    "manual",\n                    120\n                )\n                provider = payment_text(\n                    "provider",\n                    "owner_directed",\n                    120\n                )\n                payment_link = payment_text(\n                    "payment_link",\n                    "",\n                    1000\n                )\n                payment_reference = payment_text(\n                    "payment_reference",\n                    "",\n                    160\n                )\n                note = payment_text(\n                    "note",\n                    "",\n                    1000\n                )\n            except ValueError as exc:\n                return jsonify(\n                    {\n                        "ok": False,\n                        "error": str(exc),\n                    }\n                ), 400\n\n            if (\n                payment_link\n                and not payment_link.lower().startswith(\n                    ("https://", "http://")\n                )\n            ):\n                return jsonify(\n                    {\n                        "ok": False,\n                        "error": (\n                            "payment_link must start with "\n                            "http:// or https://."\n                        ),\n                    }\n                ), 400\n\n            default_amount = (\n                existing_data.get("amount_cents")\n                if existing_data\n                else order["total_cents"]\n            )\n\n            try:\n                amount_cents = int(\n                    payload.get(\n                        "amount_cents",\n                        default_amount or 0\n                    )\n                )\n            except (\n                TypeError,\n                ValueError\n            ):\n                return jsonify(\n                    {\n                        "ok": False,\n                        "error": (\n                            "amount_cents must be "\n                            "a whole number."\n                        ),\n                    }\n                ), 400\n\n            if amount_cents < 0:\n                return jsonify(\n                    {\n                        "ok": False,\n                        "error": (\n                            "amount_cents cannot "\n                            "be negative."\n                        ),\n                    }\n                ), 400\n\n            previous_status = str(\n                order["payment_status"]\n                or "unpaid"\n            ).strip().lower()\n\n            if previous_status != payment_status:\n                con.execute(\n                    """\n                    UPDATE orders\n                    SET payment_status = ?\n                    WHERE id = ?\n                    """,\n                    (\n                        payment_status,\n                        order_id,\n                    ),\n                )\n\n            con.execute(\n                """\n                INSERT INTO payment_freedom_records (\n                    order_id,\n                    payment_status,\n                    payment_method,\n                    provider,\n                    payment_link,\n                    payment_reference,\n                    amount_cents,\n                    note,\n                    updated_at\n                )\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)\n                ON CONFLICT(order_id)\n                DO UPDATE SET\n                    payment_status = excluded.payment_status,\n                    payment_method = excluded.payment_method,\n                    provider = excluded.provider,\n                    payment_link = excluded.payment_link,\n                    payment_reference = excluded.payment_reference,\n                    amount_cents = excluded.amount_cents,\n                    note = excluded.note,\n                    updated_at = CURRENT_TIMESTAMP\n                """,\n                (\n                    order_id,\n                    payment_status,\n                    payment_method,\n                    provider,\n                    payment_link,\n                    payment_reference,\n                    amount_cents,\n                    note,\n                ),\n            )\n\n            con.commit()\n\n            updated_order = con.execute(\n                """\n                SELECT *\n                FROM orders\n                WHERE id = ?\n                LIMIT 1\n                """,\n                (order_id,),\n            ).fetchone()\n\n            payment_record = con.execute(\n                """\n                SELECT *\n                FROM payment_freedom_records\n                WHERE order_id = ?\n                LIMIT 1\n                """,\n                (order_id,),\n            ).fetchone()\n\n            return jsonify(\n                {\n                    "ok": True,\n                    "changed": (\n                        previous_status\n                        != payment_status\n                    ),\n                    "previous_payment_status": (\n                        previous_status\n                    ),\n                    "payment_status": (\n                        payment_status\n                    ),\n                    "order": dict(\n                        updated_order\n                    ),\n                    "payment": dict(\n                        payment_record\n                    ),\n                }\n            )\n        finally:\n            con.close()\n\n\n'


def backup_file(source: Path, backup_root: Path) -> None:
    relative = source.relative_to(ROOT)
    destination = backup_root / relative
    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )
    shutil.copy2(source, destination)

if not BACKEND.exists():
    raise SystemExit(
        f"Backend file not found: {BACKEND}"
    )

timestamp = datetime.now().strftime(
    "%Y%m%d-%H%M%S"
)
backup_root = (
    ROOT
    / "backups"
    / "payment-freedom-engine"
    / timestamp
)

backend_text = BACKEND.read_text(
    encoding="utf-8"
)

if MARKER not in backend_text:
    if START not in backend_text:
        raise SystemExit(
            "Existing payment-status route "
            "anchor was not found."
        )

    start_index = backend_text.index(
        START
    )
    end_index = backend_text.index(
        END,
        start_index
    )

    backup_file(
        BACKEND,
        backup_root
    )

    backend_text = (
        backend_text[:start_index]
        + ROUTES
        + backend_text[end_index:]
    )

    BACKEND.write_text(
        backend_text,
        encoding="utf-8"
    )

    print(
        "Backend Payment Freedom routes added."
    )
else:
    print(
        "Backend Payment Freedom routes "
        "already present."
    )

wording_updates = 0

for source in FRONTEND_FILES:
    if not source.exists():
        continue

    original = source.read_text(
        encoding="utf-8"
    )
    updated = (
        original
        .replace("SQLite", "PostgreSQL")
        .replace("SQLITE", "POSTGRESQL")
    )

    if updated == original:
        continue

    backup_file(
        source,
        backup_root
    )
    source.write_text(
        updated,
        encoding="utf-8"
    )
    wording_updates += 1

print(
    f"Frontend database wording updated "
    f"in {wording_updates} file(s)."
)

py_compile.compile(
    str(BACKEND),
    doraise=True
)

print(
    "Backend Python compile: PASS"
)
print(
    f"Backup: {backup_root}"
)
print(
    "PAYMENT FREEDOM BACKEND V1 COMPLETE"
)
