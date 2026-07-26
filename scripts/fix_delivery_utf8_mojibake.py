from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


ROOT = Path(r"X:\i-am-the-one-saas")
SEARCH_ROOTS = [
    ROOT / "backend",
    ROOT / "frontend" / "src",
]

BACKUP_ROOT = (
    ROOT
    / "backups"
    / "delivery-utf8-fix"
    / datetime.now().strftime("%Y%m%d-%H%M%S")
)

ALLOWED_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".html",
    ".css",
    ".json",
}

REPLACEMENTS = {
    "â„¢": "™",
    "Â©": "©",
}

changed_files: list[Path] = []
replacement_count = 0

for search_root in SEARCH_ROOTS:
    if not search_root.exists():
        continue

    for path in search_root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        if any(
            blocked in path.parts
            for blocked in {
                "node_modules",
                "dist",
                ".venv",
                "__pycache__",
            }
        ):
            continue

        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"SKIPPED NON-UTF8 FILE: {path}")
            continue

        updated = original
        file_replacements = 0

        for bad_text, correct_text in REPLACEMENTS.items():
            occurrences = updated.count(bad_text)

            if occurrences:
                updated = updated.replace(bad_text, correct_text)
                file_replacements += occurrences

        if updated == original:
            continue

        relative_path = path.relative_to(ROOT)
        backup_path = BACKUP_ROOT / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)

        path.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )

        changed_files.append(path)
        replacement_count += file_replacements

        print(
            f"FIXED: {relative_path} "
            f"({file_replacements} replacement(s))"
        )

print()
print(f"Changed files: {len(changed_files)}")
print(f"Total replacements: {replacement_count}")

if changed_files:
    print(f"Backups: {BACKUP_ROOT}")
else:
    print("No corrupted source strings were found.")
