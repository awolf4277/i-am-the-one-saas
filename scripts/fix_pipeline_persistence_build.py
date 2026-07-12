from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"

APP = SRC / "App.tsx"
PIPELINE = SRC / "components" / "BuyerPipelineBoard.tsx"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Pipeline Persistence frontend repair starting...")


def backup(path: Path) -> Path:
    backup_dir = ROOT / "backups" / "pipeline-build-repair"
    backup_dir.mkdir(parents=True, exist_ok=True)

    target = backup_dir / f"{path.stem}-{stamp}{path.suffix}"

    shutil.copy2(path, target)

    print(f"Backup created: {target}")

    return target


if not APP.exists():
    raise SystemExit(f"App.tsx not found: {APP}")

if not PIPELINE.exists():
    raise SystemExit(
        f"BuyerPipelineBoard not found: {PIPELINE}"
    )


backup(APP)
backup(PIPELINE)

print()
print("Moving TypeScript backup files out of src...")

excluded_dir = ROOT / "backups" / "typescript-src-backups"

excluded_dir.mkdir(
    parents=True,
    exist_ok=True,
)

moved_count = 0

for path in list(SRC.rglob("*.tsx")):
    if ".before-" not in path.name:
        continue

    relative_name = str(
        path.relative_to(SRC)
    ).replace("\\", "__").replace("/", "__")

    target = excluded_dir / relative_name

    if target.exists():
        target = excluded_dir / (
            f"{target.stem}-{stamp}{target.suffix}"
        )

    shutil.move(
        str(path),
        str(target),
    )

    print(f"Moved build backup: {path.name}")

    moved_count += 1

print(
    f"Excluded {moved_count} backup TSX file(s) from build."
)

pipeline = PIPELINE.read_text(
    encoding="utf-8"
)

pipeline = pipeline.replace(
    """type Props = {
  setupRequests: unknown[];
  ownerToken: string;
};""",
    """type Props = {
  setupRequests: unknown[];
  ownerToken?: string;
};""",
    1,
)

old_copied = """  const [copiedKey, setCopiedKey] =
    useState("");

  const leads = useMemo<Lead[]>(() => {"""

new_copied = """  const [copiedKey, setCopiedKey] =
    useState("");

  const resolvedOwnerToken =
    ownerToken ||
    window.localStorage.getItem(
      "wolf_owner_token"
    ) ||
    "";

  const leads = useMemo<Lead[]>(() => {"""

if old_copied in pipeline:
    pipeline = pipeline.replace(
        old_copied,
        new_copied,
        1,
    )

pipeline = pipeline.replace(
    "if (!ownerToken) {",
    "if (!resolvedOwnerToken) {",
)

pipeline = pipeline.replace(
    "`Bearer ${ownerToken}`",
    "`Bearer ${resolvedOwnerToken}`",
)

pipeline = pipeline.replace(
    "}, [ownerToken, leads]);",
    "}, [resolvedOwnerToken, leads]);",
)

PIPELINE.write_text(
    pipeline,
    encoding="utf-8",
)

print("Buyer Pipeline owner token fallback repaired.")

app_text = APP.read_text(
    encoding="utf-8"
)

app_text = app_text.replace(
    "<BuyerPipelineBoard setupRequests={setupRequests} ownerToken={ownerToken} />",
    "<BuyerPipelineBoard setupRequests={setupRequests} />",
    1,
)

APP.write_text(
    app_text,
    encoding="utf-8",
)

print("Deal Desk render repaired.")

print()
print("Running frontend build...")

npm_command = (
    "npm.cmd"
    if sys.platform.startswith("win")
    else "npm"
)

result = subprocess.run(
    [
        npm_command,
        "run",
        "build",
    ],
    cwd=FRONTEND,
    text=True,
)

if result.returncode != 0:
    raise SystemExit(
        "Frontend build still failed. Review the TypeScript error above."
    )

print()
print("SUCCESS: PIPELINE PERSISTENCE BUILD REPAIRED.")
print("SQLite backend pipeline routes remain installed.")
print("Deal Desk now reads the saved owner token.")
print("TypeScript backup files were moved out of frontend/src.")
