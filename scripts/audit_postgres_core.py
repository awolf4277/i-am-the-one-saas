from pathlib import Path
import re
import subprocess

root = Path(r"X:\i-am-the-one-saas")
source_root = root / "backend" / "app"
output = root / "postgres-core-audit.txt"

patterns = {
    "sqlite import": re.compile(r"\b(?:import sqlite3|from sqlite3)\b", re.I),
    "sqlite row": re.compile(r"\bsqlite3\.Row\b|\brow_factory\b", re.I),
    "pragma": re.compile(r"\bPRAGMA\b", re.I),
    "autoincrement": re.compile(r"\bAUTOINCREMENT\b", re.I),
    "insert or ignore": re.compile(r"\bINSERT\s+OR\s+IGNORE\b", re.I),
    "insert or replace": re.compile(r"\bINSERT\s+OR\s+REPLACE\b", re.I),
    "begin immediate": re.compile(r"\bBEGIN\s+IMMEDIATE\b", re.I),
    "lastrowid": re.compile(r"\blastrowid\b", re.I),
    "sqlite master": re.compile(r"\bsqlite_master\b", re.I),
    "question placeholder": re.compile(r"\?"),
}

def is_real_source(path: Path) -> bool:
    lowered = str(path).lower()

    excluded_parts = (
        ".venv",
        "__pycache__",
        "backups",
        "_backups",
        "site-packages",
    )

    if any(part in lowered for part in excluded_parts):
        return False

    if ".before-" in path.name.lower():
        return False

    return path.suffix.lower() == ".py"

try:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"],
        cwd=root,
        text=True,
    ).strip()
except Exception:
    branch = "unknown"

files = [
    path
    for path in sorted(source_root.rglob("*.py"))
    if is_real_source(path)
]

total_hits = 0

with output.open("w", encoding="utf-8") as handle:
    handle.write("WOLF OS PostgreSQL Core Audit\n")
    handle.write(f"Branch: {branch}\n")
    handle.write(f"Source root: {source_root}\n")
    handle.write(f"Files scanned: {len(files)}\n\n")

    for path in files:
        lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

        hits = []

        for line_number, line in enumerate(lines, 1):
            labels = [
                label
                for label, pattern in patterns.items()
                if pattern.search(line)
            ]

            if labels:
                hits.append((line_number, labels))

        if not hits:
            continue

        total_hits += len(hits)
        relative = path.relative_to(root)

        handle.write("=" * 78 + "\n")
        handle.write(f"FILE: {relative}\n")
        handle.write(f"HITS: {len(hits)}\n")
        handle.write("=" * 78 + "\n")

        printed_lines = set()

        for line_number, labels in hits:
            start = max(1, line_number - 3)
            end = min(len(lines), line_number + 3)

            handle.write(
                f"\nMATCH {line_number}: {', '.join(labels)}\n"
            )

            for current in range(start, end + 1):
                key = (relative, current)

                if key in printed_lines:
                    continue

                printed_lines.add(key)
                marker = ">" if current == line_number else " "
                handle.write(
                    f"{marker} {current:5}: {lines[current - 1]}\n"
                )

        handle.write("\n")

    handle.write("=" * 78 + "\n")
    handle.write(f"TOTAL SOURCE HITS: {total_hits}\n")

print(f"Branch: {branch}")
print(f"Scanned {len(files)} real application files.")
print(f"Found {total_hits} migration-related source hits.")
print(f"Clean report: {output}")
