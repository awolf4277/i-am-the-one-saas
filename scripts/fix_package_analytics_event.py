from pathlib import Path
import re
import sys


app_path = Path(r"X:\i-am-the-one-saas\frontend\src\App.tsx")

if not app_path.exists():
    print(f"ERROR: File not found: {app_path}")
    raise SystemExit(1)

text = app_path.read_text(encoding="utf-8")

event_name = '"setup_package_select"'

if event_name in text:
    print("setup_package_select is already declared.")
    raise SystemExit(0)

pattern = re.compile(
    r"(type\s+AnalyticsEventName\s*=\s*)(.*?)(;)",
    re.DOTALL,
)

match = pattern.search(text)

if not match:
    print("ERROR: AnalyticsEventName type was not found.")
    raise SystemExit(1)

existing_events = match.group(2).rstrip()

updated_events = (
    existing_events
    + '\n  | "setup_package_select"'
)

replacement = (
    match.group(1)
    + updated_events
    + match.group(3)
)

text = text[:match.start()] + replacement + text[match.end():]

app_path.write_text(text, encoding="utf-8", newline="\n")

print("Added setup_package_select to AnalyticsEventName.")
print(f"Updated: {app_path}")
