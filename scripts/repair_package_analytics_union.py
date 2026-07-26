from pathlib import Path
import re


APP_PATH = Path(r"X:\i-am-the-one-saas\frontend\src\App.tsx")
EVENT = '"setup_package_select"'

if not APP_PATH.exists():
    raise SystemExit(f"ERROR: File not found: {APP_PATH}")

text = APP_PATH.read_text(encoding="utf-8")

pattern = re.compile(
    r"type\s+AnalyticsEventName\s*=\s*.*?;",
    re.DOTALL,
)

matches = list(pattern.finditer(text))

if len(matches) == 0:
    raise SystemExit("ERROR: AnalyticsEventName declaration was not found.")

if len(matches) > 1:
    raise SystemExit(
        f"ERROR: Found {len(matches)} AnalyticsEventName declarations; refusing an unsafe edit."
    )

match = matches[0]
declaration = match.group(0)

if EVENT in declaration:
    print("setup_package_select is already inside AnalyticsEventName.")
else:
    repaired = declaration[:-1].rstrip() + f"\n  | {EVENT};"

    text = (
        text[:match.start()]
        + repaired
        + text[match.end():]
    )

    APP_PATH.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    print("Added setup_package_select to AnalyticsEventName.")

print(f"Updated: {APP_PATH}")
