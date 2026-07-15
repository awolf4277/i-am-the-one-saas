from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
APP = ROOT / "frontend" / "src" / "App.tsx"
FRONTEND = ROOT / "frontend"

def fail(message: str) -> None:
    print(f"\nERROR: {message}")
    sys.exit(1)

if not APP.exists():
    fail(f"App.tsx not found: {APP}")

text = APP.read_text(encoding="utf-8")
original = text

if "async function updateOrderPaymentStatus(" not in text:
    fail("The existing updateOrderPaymentStatus function was not found.")

if "function OwnerConsole" not in text:
    fail("The OwnerConsole component was not found.")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = APP.with_name(f"App.before-owner-payment-prop-{stamp}.tsx")
shutil.copy2(APP, backup)
print(f"Backup created: {backup}")

# 1) Pass the existing App-level function into OwnerConsole.
if "onUpdateOrderPaymentStatus={updateOrderPaymentStatus}" not in text:
    anchor = "onUpdateStock={updateProductStock}"
    if anchor not in text:
        fail(f"Could not find OwnerConsole render anchor: {anchor}")

    text = text.replace(
        anchor,
        anchor + "\n            onUpdateOrderPaymentStatus={updateOrderPaymentStatus}",
        1,
    )
    print("Connected updateOrderPaymentStatus to OwnerConsole.")

# 2) Add the callback to the OwnerConsole prop type.
if not re.search(r"\bonUpdateOrderPaymentStatus\s*:", text):
    match = re.search(
        r"(?m)^(?P<indent>\s*)onUpdateStock\s*:\s*[^;]+;\s*$",
        text,
    )
    if not match:
        fail("Could not find the onUpdateStock prop type.")

    insertion = (
        match.group(0)
        + "\n"
        + match.group("indent")
        + 'onUpdateOrderPaymentStatus: (\n'
        + match.group("indent")
        + '  orderId: string,\n'
        + match.group("indent")
        + '  paymentStatus: "paid" | "unpaid"\n'
        + match.group("indent")
        + ') => Promise<void>;'
    )
    text = text[: match.start()] + insertion + text[match.end() :]
    print("Added OwnerConsole payment callback type.")

# 3) Destructure the callback inside OwnerConsole.
owner_start = text.find("function OwnerConsole")
owner_signature_end = text.find(") {", owner_start)
if owner_signature_end == -1:
    owner_signature_end = text.find("}: ", owner_start)
if owner_signature_end == -1:
    fail("Could not locate the end of the OwnerConsole signature.")

signature = text[owner_start:owner_signature_end]

if "onUpdateOrderPaymentStatus" not in signature:
    signature_new, count = re.subn(
        r"(?m)^(?P<indent>\s*)onUpdateStock,\s*$",
        lambda m: (
            m.group(0)
            + "\n"
            + m.group("indent")
            + "onUpdateOrderPaymentStatus,"
        ),
        signature,
        count=1,
    )
    if count != 1:
        fail("Could not add onUpdateOrderPaymentStatus to OwnerConsole destructuring.")

    text = (
        text[:owner_start]
        + signature_new
        + text[owner_signature_end:]
    )
    print("Added payment callback to OwnerConsole parameters.")

# 4) Use the prop inside OwnerConsole instead of the out-of-scope App function.
owner_start = text.find("function OwnerConsole")
before_owner = text[:owner_start]
owner_code = text[owner_start:]

replacement_count = owner_code.count("updateOrderPaymentStatus(")
owner_code = owner_code.replace(
    "updateOrderPaymentStatus(",
    "onUpdateOrderPaymentStatus(",
)

if replacement_count < 2 and "onUpdateOrderPaymentStatus(" not in owner_code:
    fail("Expected payment button calls were not found inside OwnerConsole.")

text = before_owner + owner_code

if text == original:
    print("No changes were necessary; wiring already appears installed.")
else:
    APP.write_text(text, encoding="utf-8")
    print("Owner payment callback wiring installed.")

print("\nRunning frontend build...\n")
result = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
    text=True,
)

if result.returncode != 0:
    print("\nFrontend build failed.")
    print(f"Restore backup if needed: {backup}")
    sys.exit(result.returncode)

print("\nSUCCESS: Frontend build passed.")
print("Revenue Action Center remains installed.")
print("Restart Vite if needed, then hard-refresh the Owner Console.")