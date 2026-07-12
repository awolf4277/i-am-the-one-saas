from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

BACKEND_APP = BACKEND / "app" / "__init__.py"

ACTIVITY_COMPONENT = (
    FRONTEND
    / "src"
    / "components"
    / "DealActivityTimeline.tsx"
)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Deal Activity route repair starting...")


def backup(path: Path, name: str) -> None:
    backup_dir = ROOT / "backups" / "activity-route-repair"

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = backup_dir / (
        f"{name}-{stamp}{path.suffix}"
    )

    shutil.copy2(
        path,
        target,
    )

    print(f"Backup created: {target}")


if not BACKEND_APP.exists():
    raise SystemExit(
        f"Backend app not found: {BACKEND_APP}"
    )

if not ACTIVITY_COMPONENT.exists():
    raise SystemExit(
        "DealActivityTimeline.tsx not found."
    )


backup(
    BACKEND_APP,
    "backend-init",
)

backup(
    ACTIVITY_COMPONENT,
    "DealActivityTimeline",
)


backend = BACKEND_APP.read_text(
    encoding="utf-8"
)


new_route = '''    @app.get("/api/owner/pipeline-activity")
    def owner_pipeline_activity_log():
        ok, error = require_owner()

        if not ok:
            return error

        lead_id = str(
            request.args.get("lead_id") or ""
        ).strip()

        try:
            limit = int(
                request.args.get("limit") or 50
            )
        except (TypeError, ValueError):
            limit = 50

        limit = max(
            1,
            min(limit, 200),
        )

        con = connect(app)

        try:
            params = []

            sql = """
                SELECT
                    pa.id,
                    pa.lead_id,
                    pa.activity_type,
                    pa.old_value,
                    pa.new_value,
                    pa.summary,
                    pa.created_at,
                    sr.business_name,
                    sr.name,
                    sr.email
                FROM pipeline_activity pa
                LEFT JOIN setup_requests sr
                    ON sr.id = pa.lead_id
            """

            if lead_id:
                sql += """
                    WHERE pa.lead_id = ?
                """

                params.append(lead_id)

            sql += """
                ORDER BY pa.created_at DESC
                LIMIT ?
            """

            params.append(limit)

            rows = con.execute(
                sql,
                tuple(params),
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "count": len(rows),
                    "activities": [
                        dict(row)
                        for row in rows
                    ],
                }
            )

        finally:
            con.close()

'''


if (
    '@app.get("/api/owner/pipeline-activity")'
    not in backend
):
    anchor = (
        '    @app.get("/api/owner/pipeline")'
    )

    position = backend.find(anchor)

    if position < 0:
        raise SystemExit(
            "Could not locate owner pipeline route anchor."
        )

    backend = (
        backend[:position]
        + new_route
        + backend[position:]
    )

    print(
        "Added non-conflicting pipeline activity route."
    )

else:
    print(
        "Pipeline activity repair route already exists."
    )


BACKEND_APP.write_text(
    backend,
    encoding="utf-8",
)


frontend = ACTIVITY_COMPONENT.read_text(
    encoding="utf-8"
)

old_url = (
    "${API_BASE}/api/owner/pipeline/activity?limit=40"
)

new_url = (
    "${API_BASE}/api/owner/pipeline-activity?limit=40"
)

if old_url in frontend:
    frontend = frontend.replace(
        old_url,
        new_url,
        1,
    )

    print(
        "Frontend Activity API URL repaired."
    )

elif new_url in frontend:
    print(
        "Frontend already uses repaired Activity URL."
    )

else:
    raise SystemExit(
        "Could not locate Deal Activity API URL."
    )


ACTIVITY_COMPONENT.write_text(
    frontend,
    encoding="utf-8",
)


print()
print("Checking exact Flask route methods...")


backend_python = (
    BACKEND
    / ".venv"
    / "Scripts"
    / "python.exe"
)

route_check = subprocess.run(
    [
        str(backend_python),
        "-c",
        (
            "import wsgi; "
            "rules=[r for r in "
            "wsgi.app.url_map.iter_rules() "
            "if str(r)=='/api/owner/pipeline-activity']; "
            "assert rules, 'activity route missing'; "
            "assert 'GET' in rules[0].methods, "
            "f'GET missing: {rules[0].methods}'; "
            "print('ACTIVITY ROUTE GET OK:', "
            "sorted(rules[0].methods))"
        ),
    ],
    cwd=BACKEND,
    text=True,
)

if route_check.returncode != 0:
    raise SystemExit(
        "Flask activity GET route verification failed."
    )


print()
print("Running frontend build...")


npm_command = (
    "npm.cmd"
    if sys.platform.startswith("win")
    else "npm"
)

build = subprocess.run(
    [
        npm_command,
        "run",
        "build",
    ],
    cwd=FRONTEND,
    text=True,
)

if build.returncode != 0:
    raise SystemExit(
        "Frontend build failed."
    )


print()
print(
    "SUCCESS: DEAL ACTIVITY ROUTE REPAIRED."
)
print(
    "Activity API now uses /api/owner/pipeline-activity."
)
print(
    "The route explicitly supports GET."
)
print(
    "Restart the Flask backend before testing."
)