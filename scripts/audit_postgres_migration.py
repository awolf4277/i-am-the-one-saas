from pathlib import Path
import re

root = Path(r"X:\i-am-the-one-saas\backend")
patterns = {
    "sqlite imports": r"\bimport sqlite3\b|\bfrom sqlite3\b",
    "question placeholders": r"\?",
    "pragma": r"\bPRAGMA\b",
    "insert or ignore": r"\bINSERT\s+OR\s+IGNORE\b",
    "insert or replace": r"\bINSERT\s+OR\s+REPLACE\b",
    "autoincrement": r"\bAUTOINCREMENT\b",
    "lastrowid": r"\blastrowid\b",
    "sqlite master": r"\bsqlite_master\b",
    "row factory": r"\brow_factory\b",
    "begin immediate": r"\bBEGIN\s+IMMEDIATE\b",
    "datetime functions": r"\bdatetime\s*\(|\bstrftime\s*\(",
}

results = []

for path in sorted(root.rglob("*.py")):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    for number, line in enumerate(lines, 1):
        for label, pattern in patterns.items():
            if re.search(pattern, line, flags=re.IGNORECASE):
                results.append(
                    (
                        str(path.relative_to(root.parent)),
                        number,
                        label,
                        line.strip(),
                    )
                )

output = Path(r"X:\i-am-the-one-saas\postgres-migration-audit.txt")

with output.open("w", encoding="utf-8") as handle:
    for filename, number, label, line in results:
        handle.write(f"{filename}:{number} [{label}] {line}\n")

print(f"Found {len(results)} PostgreSQL migration items.")
print(f"Report: {output}")
