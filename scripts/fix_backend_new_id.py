from pathlib import Path
from datetime import datetime
import shutil
import subprocess

ROOT = Path(r"X:\i-am-the-one-saas")
BACKEND = ROOT / "backend"
APP = BACKEND / "app" / "__init__.py"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS new_id NameError repair starting...")

if not APP.exists():
    raise SystemExit(f"Backend app not found: {APP}")

backup_dir = ROOT / "backups" / "new-id-repair"
backup_dir.mkdir(parents=True, exist_ok=True)

backup = backup_dir / f"backend-init-{stamp}.py"

shutil.copy2(APP, backup)

print(f"Backup created: {backup}")

text = APP.read_text(encoding="utf-8")

if "from uuid import uuid4" not in text:
    text = "from uuid import uuid4\n" + text

    print("Added uuid4 import.")
else:
    print("uuid4 import already exists.")

helper = '''def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


'''

if "def new_id(" not in text:
    anchor = "def now_iso("

    position = text.find(anchor)

    if position < 0:
        raise SystemExit(
            "PATCH STOPPED: Could not locate now_iso helper."
        )

    text = (
        text[:position]
        + helper
        + text[position:]
    )

    print("Added new_id helper.")
else:
    print("new_id helper already exists.")

APP.write_text(
    text,
    encoding="utf-8",
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
            "from app import new_id; "
            "value=new_id('ACT'); "
            "assert value.startswith('ACT-'); "
            "print('NEW ID HELPER OK:', value)"
        ),
    ],
    cwd=BACKEND,
    text=True,
)

if result.returncode != 0:
    raise SystemExit(
        "Backend new_id verification failed."
    )

print()
print("SUCCESS: BACKEND NEW_ID ERROR REPAIRED.")
print("Restart the backend before testing the unified pipeline PUT.")