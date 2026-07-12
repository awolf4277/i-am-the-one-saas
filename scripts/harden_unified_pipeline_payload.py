from pathlib import Path
from datetime import datetime
import shutil
import subprocess

ROOT = Path(r"X:\i-am-the-one-saas")
BACKEND = ROOT / "backend"
APP = BACKEND / "app" / "__init__.py"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS unified pipeline payload guard starting...")

if not APP.exists():
    raise SystemExit(
        f"Backend app not found: {APP}"
    )

backup_dir = (
    ROOT
    / "backups"
    / "unified-pipeline-payload-guard"
)

backup_dir.mkdir(
    parents=True,
    exist_ok=True,
)

backup = (
    backup_dir
    / f"backend-init-{stamp}.py"
)

shutil.copy2(
    APP,
    backup,
)

print(f"Backup created: {backup}")

text = APP.read_text(
    encoding="utf-8",
)

route_marker = (
    '@app.put('
    '"/api/owner/pipeline-state/<lead_id>"'
    ')'
)

route_position = text.find(
    route_marker
)

if route_position < 0:
    raise SystemExit(
        "PATCH STOPPED: Unified pipeline PUT route not found."
    )

block_start = text.find(
    "        payload = request.get_json(",
    route_position,
)

block_end_marker = '''        next_action = str(
            payload.get("next_action") or ""
        ).strip()
'''

block_end = text.find(
    block_end_marker,
    block_start,
)

if block_start < 0 or block_end < 0:
    raise SystemExit(
        "PATCH STOPPED: Current payload block not found."
    )

block_end += len(
    block_end_marker
)

replacement = '''        payload = request.get_json(
            silent=True
        )

        if payload is None:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Request body must contain valid JSON."
                    ),
                }
            ), 400

        if not isinstance(payload, dict):
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Pipeline payload must be a JSON object."
                    ),
                }
            ), 400

        required_fields = {
            "stage",
            "deal_value",
            "next_action",
        }

        missing_fields = sorted(
            required_fields
            - set(payload.keys())
        )

        if missing_fields:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Missing required pipeline fields: "
                        + ", ".join(missing_fields)
                    ),
                }
            ), 400

        allowed_stages = {
            "New",
            "Contacted",
            "Demo",
            "Proposal",
            "Closing",
            "Won",
            "Lost",
        }

        stage = str(
            payload["stage"]
        ).strip()

        if stage not in allowed_stages:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        f"Invalid pipeline stage: {stage}"
                    ),
                }
            ), 400

        try:
            deal_value = int(
                float(
                    payload["deal_value"]
                )
            )

        except (TypeError, ValueError):
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "deal_value must be numeric."
                    ),
                }
            ), 400

        deal_value = max(
            0,
            deal_value,
        )

        next_action = str(
            payload["next_action"]
            if payload["next_action"] is not None
            else ""
        ).strip()
'''

text = (
    text[:block_start]
    + replacement
    + text[block_end:]
)

APP.write_text(
    text,
    encoding="utf-8",
)

print(
    "Unified pipeline PUT now rejects malformed "
    "or incomplete payloads."
)

print()
print("Checking backend import...")

python = (
    BACKEND
    / ".venv"
    / "Scripts"
    / "python.exe"
)

result = subprocess.run(
    [
        str(python),
        "-c",
        (
            "import wsgi; "
            "routes=[str(rule) for rule in "
            "wsgi.app.url_map.iter_rules()]; "
            "assert '/api/owner/pipeline-state/<lead_id>' "
            "in routes; "
            "print('PIPELINE PAYLOAD GUARD IMPORT OK')"
        ),
    ],
    cwd=BACKEND,
    text=True,
)

if result.returncode != 0:
    raise SystemExit(
        "Backend verification failed."
    )

print()
print(
    "SUCCESS: UNIFIED PIPELINE PAYLOAD GUARD INSTALLED."
)
print(
    "Malformed JSON can no longer silently reset a deal."
)
