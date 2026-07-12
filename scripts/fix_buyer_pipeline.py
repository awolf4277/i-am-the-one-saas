from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND = ROOT / "frontend"
PATH = FRONTEND / "src" / "components" / "BuyerPipelineBoard.tsx"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Buyer Pipeline repair starting...")

if not PATH.exists():
    raise SystemExit(f"BuyerPipelineBoard not found: {PATH}")

backup = PATH.with_name(
    f"BuyerPipelineBoard.before-repair-{stamp}.tsx"
)

shutil.copy2(PATH, backup)

print(f"Backup created: {backup}")

text = PATH.read_text(encoding="utf-8-sig")

# Repair UTF-8 mojibake without putting special symbols
# directly inside this Python repair script.
text = text.replace(
    "\u00e2\u201e\u00a2",
    "\u2122",
)

text = text.replace(
    "\u00c2\u00b7",
    "\u00b7",
)

# Force a fresh pipeline cache after fixing budget detection.
text = text.replace(
    'const STORAGE_KEY = "wolf-os-buyer-pipeline-v1";',
    'const STORAGE_KEY = "wolf-os-buyer-pipeline-v2";',
)

old_budget = '''      const budget = valueText(
        lead,
        ["budget", "package", "package_interest"],
        "Package not selected"
      );
'''

new_budget = '''      const budget = valueText(
        lead,
        [
          "budget",
          "budget_range",
          "budgetRange",
          "budget_level",
          "budgetLevel",
          "project_budget",
          "projectBudget",
          "package",
          "package_interest",
          "packageInterest",
          "selected_package",
          "selectedPackage",
          "package_name",
          "packageName",
        ],
        Object.entries(lead)
          .filter(([key]) => /budget|package/i.test(key))
          .map(([, value]) =>
            typeof value === "string" ||
            typeof value === "number"
              ? String(value).trim()
              : ""
          )
          .find(Boolean) || "Package not selected"
      );
'''

if old_budget in text:
    text = text.replace(old_budget, new_budget)

    print("Expanded live lead budget detection.")
else:
    print(
        "WARNING: Original budget block not found. "
        "Encoding repairs will still be applied."
    )

PATH.write_text(text, encoding="utf-8")

print("Repaired trademark display.")
print("Repaired buyer separator display.")
print("Advanced pipeline storage to v2.")

print()
print("Running frontend build...")

npm_command = (
    "npm.cmd"
    if sys.platform.startswith("win")
    else "npm"
)

result = subprocess.run(
    [npm_command, "run", "build"],
    cwd=FRONTEND,
    text=True,
)

if result.returncode != 0:
    raise SystemExit(
        "Frontend build failed. "
        f"Backup remains at: {backup}"
    )

print()
print("SUCCESS: BUYER PIPELINE DISPLAY REPAIRED.")
print("Refresh the Owner Console.")
print("Confirm lead budgets and WOLF OS text display correctly.")