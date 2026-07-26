from pathlib import Path
import subprocess

root = Path(r"X:\i-am-the-one-saas")

files = [
    root / "backend" / "app" / "__init__.py",
    root / "backend" / "app" / "db.py",
    root / "backend" / "app" / "routes" / "analytics.py",
    root / "backend" / "app" / "routes" / "checkout.py",
    root / "backend" / "app" / "routes" / "orders.py",
    root / "backend" / "app" / "routes" / "products.py",
    root / "backend" / "app" / "routes" / "stores.py",
    root / "backend" / "requirements.txt",
    root / "backend" / "wsgi.py",
]

output = root / "postgres-source-bundle.txt"

try:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"],
        cwd=root,
        text=True,
    ).strip()
except Exception:
    branch = "unknown"

with output.open("w", encoding="utf-8") as handle:
    handle.write("WOLF OS POSTGRESQL SOURCE BUNDLE\n")
    handle.write(f"BRANCH: {branch}\n")
    handle.write("=" * 90 + "\n\n")

    for path in files:
        relative = path.relative_to(root)

        handle.write("\n")
        handle.write("#" * 90 + "\n")
        handle.write(f"FILE: {relative}\n")
        handle.write("#" * 90 + "\n")

        if not path.exists():
            handle.write("[FILE NOT FOUND]\n")
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        for number, line in enumerate(text.splitlines(), 1):
            handle.write(f"{number:5}: {line}\n")

print(f"Created: {output}")
print(f"Branch: {branch}")
print(f"Size: {output.stat().st_size:,} bytes")
