from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil


ROOT = Path(r"X:\i-am-the-one-saas")
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"
ENV_EXAMPLE_PATH = ROOT / "frontend" / ".env.example"

BACKUP_ROOT = (
    ROOT
    / "backups"
    / "owner-directed-payments"
    / datetime.now().strftime("%Y%m%d-%H%M%S")
)

MARKER = "WOLF_OWNER_DIRECTED_PAYMENTS_V1"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


if not APP_PATH.exists():
    fail(f"Missing file: {APP_PATH}")

BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
shutil.copy2(APP_PATH, BACKUP_ROOT / "App.tsx")

if ENV_EXAMPLE_PATH.exists():
    shutil.copy2(
        ENV_EXAMPLE_PATH,
        BACKUP_ROOT / ".env.example",
    )

text = APP_PATH.read_text(encoding="utf-8")

if MARKER in text:
    print("Owner-directed payment flow is already installed.")
    raise SystemExit(0)


# Remove obsolete Clover frontend constants.
text = re.sub(
    r'^const CLOVER_[A-Z_]+ = String\(import\.meta\.env\.[\s\S]*?\);\r?\n',
    "",
    text,
    flags=re.MULTILINE,
)


payment_start = text.find("function PaymentOptions() {")
selection_start = text.find(
    "type SetupPackageSelection = {",
    payment_start,
)

if payment_start == -1:
    fail("PaymentOptions was not found.")

if selection_start == -1:
    fail("SetupPackageSelection was not found.")


new_payment_component = r'''// WOLF_OWNER_DIRECTED_PAYMENTS_V1
function PaymentOptions() {
  const requestPaymentInstructions = (
    selection: SetupPackageSelection
  ) => {
    selectSetupPackage(selection);

    const status = document.getElementById(
      "deposit-link-status"
    );

    if (status) {
      status.textContent =
        `${selection.name} selected. ` +
        `${selection.deposit} deposit required. ` +
        "Complete the setup form to receive payment instructions directly from Andrew.";

      status.removeAttribute("hidden");
    }
  };

  return (
    <div className="shine-box payment-options-box">
      <strong>Owner-Directed Payment Options</strong>

      <span>
        Payment instructions are provided directly by Andrew
        after package selection and scope confirmation.
      </span>

      <span>
        Accepted methods may include check, cash, or bank
        transfer. The final method is confirmed privately for
        each approved project.
      </span>

      <div className="metric-list">
        <Metric label="Check" value="Available" />
        <Metric label="Cash" value="Available" />
        <Metric label="Bank Transfer" value="Available" />
      </div>

      <div className="landing-actions payment-actions">
        <button
          type="button"
          className="v3-button primary"
          onClick={() =>
            requestPaymentInstructions({
              name: "Starter Storefront",
              budget: "$1,500+ Starter",
              deposit: "$750",
              message:
                "I selected the Starter Storefront ($1,500+) and need payment instructions. I understand the required starting deposit is $750."
            })
          }
        >
          Request Starter Instructions · $750
        </button>

        <button
          type="button"
          className="v3-button secondary"
          onClick={() =>
            requestPaymentInstructions({
              name: "Pro Storefront + Dashboard",
              budget: "$4,500+ Pro",
              deposit: "$2,250",
              message:
                "I selected the Pro Storefront + Dashboard ($4,500+) and need payment instructions. I understand the required starting deposit is $2,250."
            })
          }
        >
          Request Pro Instructions · $2,250
        </button>

        <button
          type="button"
          className="v3-button secondary"
          onClick={() =>
            requestPaymentInstructions({
              name: "Custom SaaS Buildout",
              budget: "$9,000+ Custom",
              deposit: "$4,500",
              message:
                "I selected the Custom SaaS Buildout ($9,000+) and need payment instructions after scope confirmation. I understand the required deposit is $4,500."
            })
          }
        >
          Request Custom Instructions · $4,500
        </button>
      </div>

      <span
        id="deposit-link-status"
        className="close-kit-status"
        hidden
      >
        Payment-instruction request added. Complete the setup
        form and send your request.
      </span>

      <span>
        Custom work begins only after the agreed deposit has
        been received and confirmed.
      </span>
    </div>
  );
}


'''

text = (
    text[:payment_start]
    + new_payment_component
    + text[selection_start:]
)


replacements = {
    (
        "Preferred payment/deposit method, including Clover "
        "link if available"
    ): (
        "Preferred payment or deposit method, including check, "
        "cash, or bank transfer"
    ),
    (
        "<strong>Can this use Clover?</strong> Yes. Start with "
        "secure Clover payment links, then upgrade to deeper "
        "checkout later."
    ): (
        "<strong>How are payments handled?</strong> Andrew "
        "confirms the accepted payment method directly after "
        "package and scope review."
    ),
}

for old, new in replacements.items():
    text = text.replace(old, new)


APP_PATH.write_text(
    text,
    encoding="utf-8",
    newline="\n",
)


if ENV_EXAMPLE_PATH.exists():
    env_text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    env_lines = [
        line
        for line in env_text.splitlines()
        if not line.startswith("VITE_CLOVER_")
        and not line.startswith("VITE_STRIPE_")
        and not line.startswith("VITE_PAYMENT_")
    ]

    ENV_EXAMPLE_PATH.write_text(
        "\n".join(env_lines).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )


print("Owner-directed payment flow installed.")
print(f"Backups: {BACKUP_ROOT}")
print(f"Updated: {APP_PATH}")
print(f"Updated: {ENV_EXAMPLE_PATH}")
