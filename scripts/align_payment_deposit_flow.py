from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


ROOT = Path(r"X:\i-am-the-one-saas")
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"
ENV_EXAMPLE_PATH = ROOT / "frontend" / ".env.example"

BACKUP_ROOT = (
    ROOT
    / "backups"
    / "payment-deposit-alignment"
    / datetime.now().strftime("%Y%m%d-%H%M%S")
)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def replace_expected(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    if old in text:
        return text.replace(old, new)

    if new in text:
        print(f"ALREADY UPDATED: {label}")
        return text

    fail(f"Could not find expected text for: {label}")
    return text


if not APP_PATH.exists():
    fail(f"Missing file: {APP_PATH}")

BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

app_backup = BACKUP_ROOT / "App.tsx"
shutil.copy2(APP_PATH, app_backup)

if ENV_EXAMPLE_PATH.exists():
    shutil.copy2(
        ENV_EXAMPLE_PATH,
        BACKUP_ROOT / ".env.example",
    )

text = APP_PATH.read_text(encoding="utf-8")

# Add Custom deposit-link environment support.
if "VITE_CLOVER_CUSTOM_DEPOSIT_LINK" not in text:
    lines = text.splitlines(keepends=True)
    insert_index = None

    for index, line in enumerate(lines):
        if line.strip().startswith(
            "const CLOVER_PRO_DEPOSIT_LINK"
        ):
            insert_index = index + 1
            break

    if insert_index is None:
        fail("Could not find CLOVER_PRO_DEPOSIT_LINK.")

    lines.insert(
        insert_index,
        (
            "const CLOVER_CUSTOM_DEPOSIT_LINK = "
            'String(import.meta.env.'
            'VITE_CLOVER_CUSTOM_DEPOSIT_LINK || "");\n'
        ),
    )

    text = "".join(lines)

# Align package-selection deposits with the existing 50% model.
replacements = [
    (
        'deposit: "$250",',
        'deposit: "$750",',
        "Starter package deposit value",
    ),
    (
        "starting deposit is $250.",
        "starting deposit is $750.",
        "Starter package deposit message",
    ),
    (
        'deposit: "$1,000",',
        'deposit: "$2,250",',
        "Pro package deposit value",
    ),
    (
        "starting deposit is $1,000.",
        "starting deposit is $2,250.",
        "Pro package deposit message",
    ),
    (
        'deposit: "30%",',
        'deposit: "$4,500",',
        "Custom package deposit value",
    ),
    (
        "begin with a 30% deposit after scope confirmation.",
        (
            "begin with a $4,500 deposit (50%) "
            "after scope confirmation."
        ),
        "Custom package deposit message",
    ),
    (
        "Starter Storefront: $250 to begin",
        "Starter Storefront: $750 to begin",
        "Starter deposit display",
    ),
    (
        "Pro Storefront + Dashboard: $1,000 to begin",
        "Pro Storefront + Dashboard: $2,250 to begin",
        "Pro deposit display",
    ),
    (
        "Custom SaaS Buildout: 30% after scope confirmation",
        (
            "Custom SaaS Buildout: "
            "$4,500 (50%) after scope confirmation"
        ),
        "Custom deposit display",
    ),
]

for old, new, label in replacements:
    text = replace_expected(text, old, new, label)

# Replace the old Starter-only payment component.
payment_start = text.find("function PaymentOptions() {")
selection_start = text.find(
    "type SetupPackageSelection = {",
    payment_start,
)

if payment_start == -1:
    fail("PaymentOptions function was not found.")

if selection_start == -1:
    fail("SetupPackageSelection type was not found.")

new_payment_component = '''function PaymentOptions() {
  const requestPaymentLink = (
    selection: SetupPackageSelection
  ) => {
    selectSetupPackage(selection);

    const status = document.getElementById(
      "deposit-link-status"
    );

    if (status) {
      status.textContent =
        `${selection.name} selected. ` +
        `${selection.deposit} deposit-link request added. ` +
        "Complete your contact details and send the request.";

      status.removeAttribute("hidden");
    }
  };

  const hasAnyCloverLink = Boolean(
    CLOVER_STARTER_DEPOSIT_LINK ||
      CLOVER_STARTER_FULL_LINK ||
      CLOVER_PRO_DEPOSIT_LINK ||
      CLOVER_CUSTOM_DEPOSIT_LINK
  );

  return (
    <div className="shine-box payment-options-box">
      <strong>Secure Payment Options</strong>

      <span>
        Select a package first. When its secure Clover link
        is configured, the buyer can pay the deposit directly.
        Otherwise, the request is added to the setup form for
        Andrew to review.
      </span>

      <div className="landing-actions payment-actions">
        {CLOVER_STARTER_DEPOSIT_LINK ? (
          <a
            className="v3-button primary"
            href={CLOVER_STARTER_DEPOSIT_LINK}
            target="_blank"
            rel="noreferrer"
          >
            Pay Starter Deposit · $750
          </a>
        ) : (
          <button
            type="button"
            className="v3-button primary"
            onClick={() =>
              requestPaymentLink({
                name: "Starter Storefront",
                budget: "$1,500+ Starter",
                deposit: "$750",
                message:
                  "I selected the Starter Storefront ($1,500+) and need the secure $750 deposit payment link."
              })
            }
          >
            Request Starter Deposit Link · $750
          </button>
        )}

        {CLOVER_STARTER_FULL_LINK ? (
          <a
            className="v3-button secondary"
            href={CLOVER_STARTER_FULL_LINK}
            target="_blank"
            rel="noreferrer"
          >
            Pay Starter in Full · $1,500
          </a>
        ) : null}

        {CLOVER_PRO_DEPOSIT_LINK ? (
          <a
            className="v3-button primary"
            href={CLOVER_PRO_DEPOSIT_LINK}
            target="_blank"
            rel="noreferrer"
          >
            Pay Pro Deposit · $2,250
          </a>
        ) : (
          <button
            type="button"
            className="v3-button secondary"
            onClick={() =>
              requestPaymentLink({
                name: "Pro Storefront + Dashboard",
                budget: "$4,500+ Pro",
                deposit: "$2,250",
                message:
                  "I selected the Pro Storefront + Dashboard ($4,500+) and need the secure $2,250 deposit payment link."
              })
            }
          >
            Request Pro Deposit Link · $2,250
          </button>
        )}

        {CLOVER_CUSTOM_DEPOSIT_LINK ? (
          <a
            className="v3-button primary"
            href={CLOVER_CUSTOM_DEPOSIT_LINK}
            target="_blank"
            rel="noreferrer"
          >
            Pay Custom Deposit · $4,500
          </a>
        ) : (
          <button
            type="button"
            className="v3-button secondary"
            onClick={() =>
              requestPaymentLink({
                name: "Custom SaaS Buildout",
                budget: "$9,000+ Custom",
                deposit: "$4,500",
                message:
                  "I selected the Custom SaaS Buildout ($9,000+) and need the secure $4,500 deposit payment link after scope confirmation."
              })
            }
          >
            Request Custom Deposit Link · $4,500
          </button>
        )}
      </div>

      <span
        id="deposit-link-status"
        className="close-kit-status"
        hidden
      >
        Payment-link request added. Complete the setup form
        and send your request.
      </span>

      {!hasAnyCloverLink ? (
        <span>
          No public Clover links are configured yet. Buyers can
          still select a package and request the correct secure
          payment link through the setup form.
        </span>
      ) : (
        <span>
          Secure Clover links are available for the configured
          package options.
        </span>
      )}
    </div>
  );
}


'''

text = (
    text[:payment_start]
    + new_payment_component
    + text[selection_start:]
)

APP_PATH.write_text(
    text,
    encoding="utf-8",
    newline="\n",
)

# Document every supported frontend variable without setting real URLs.
env_variables = [
    "VITE_CLOVER_STARTER_DEPOSIT_LINK=",
    "VITE_CLOVER_STARTER_FULL_LINK=",
    "VITE_CLOVER_PRO_DEPOSIT_LINK=",
    "VITE_CLOVER_CUSTOM_DEPOSIT_LINK=",
]

if ENV_EXAMPLE_PATH.exists():
    env_text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
else:
    env_text = ""

for variable in env_variables:
    variable_name = variable.split("=", 1)[0]

    if variable_name not in env_text:
        if env_text and not env_text.endswith("\n"):
            env_text += "\n"

        env_text += variable + "\n"

ENV_EXAMPLE_PATH.write_text(
    env_text,
    encoding="utf-8",
    newline="\n",
)

print("Payment and deposit flow aligned.")
print(f"App backup: {app_backup}")
print(f"Updated: {APP_PATH}")
print(f"Updated: {ENV_EXAMPLE_PATH}")
