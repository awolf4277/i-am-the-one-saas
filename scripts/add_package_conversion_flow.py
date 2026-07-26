from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(r"X:\i-am-the-one-saas")
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"
BACKUP_DIR = ROOT / "backups" / "package-conversion"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)

    if count == 0:
        fail(f"Could not find anchor for {label}.")

    if count > 1:
        fail(f"Found {count} possible anchors for {label}; refusing an unsafe edit.")

    return text.replace(old, new, 1)


if not APP_PATH.exists():
    fail(f"App.tsx not found: {APP_PATH}")

original = APP_PATH.read_text(encoding="utf-8")

if "wolfos:select-setup-package" in original:
    print("Package conversion flow is already installed. No changes made.")
    raise SystemExit(0)

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

backup_path = BACKUP_DIR / f"App.before-package-conversion-{timestamp}.tsx"
shutil.copy2(APP_PATH, backup_path)

text = original

# Ensure React useEffect is available without disturbing the existing import.
has_use_effect_import = re.search(
    r'import[^;]*\buseEffect\b[^;]*from\s+["\']react["\']',
    text,
)

if not has_use_effect_import:
    text = 'import { useEffect } from "react";\n' + text


old_package_block = '''        <div className="metric-list">
          <Metric label="Starter Storefront" value="$1,500+" />
          <Metric label="Pro Storefront + Dashboard" value="$4,500+" />
          <Metric label="Custom SaaS Buildout" value="$9,000+" />
        </div>
'''

new_package_block = '''        <div className="metric-list">
          <Metric label="Starter Storefront" value="$1,500+" />
          <Metric label="Pro Storefront + Dashboard" value="$4,500+" />
          <Metric label="Custom SaaS Buildout" value="$9,000+" />
        </div>

        <div className="landing-actions">
          <button
            type="button"
            className="v3-button secondary"
            onClick={() =>
              selectSetupPackage({
                name: "Starter Storefront",
                budget: "$1,500+ Starter",
                deposit: "$250",
                message:
                  "I selected the Starter Storefront ($1,500+). I understand the starting deposit is $250."
              })
            }
          >
            Choose Starter · $1,500+
          </button>

          <button
            type="button"
            className="v3-button primary"
            onClick={() =>
              selectSetupPackage({
                name: "Pro Storefront + Dashboard",
                budget: "$4,500+ Pro",
                deposit: "$1,000",
                message:
                  "I selected the Pro Storefront + Dashboard ($4,500+). I understand the starting deposit is $1,000."
              })
            }
          >
            Choose Pro · $4,500+
          </button>

          <button
            type="button"
            className="v3-button secondary"
            onClick={() =>
              selectSetupPackage({
                name: "Custom SaaS Buildout",
                budget: "$9,000+ Custom",
                deposit: "30%",
                message:
                  "I selected the Custom SaaS Buildout ($9,000+). I understand custom projects begin with a 30% deposit after scope confirmation."
              })
            }
          >
            Discuss Custom · $9,000+
          </button>
        </div>

        <div className="shine-box">
          <strong>Starting deposits</strong>
          <span>Starter Storefront: $250 to begin</span>
          <span>Pro Storefront + Dashboard: $1,000 to begin</span>
          <span>Custom SaaS Buildout: 30% after scope confirmation</span>
        </div>
'''

text = replace_once(
    text,
    old_package_block,
    new_package_block,
    "landing package actions",
)


setup_form_anchor = '''function SetupRequestForm() {
'''

setup_package_bridge = '''type SetupPackageSelection = {
  name: string;
  budget: "$1,500+ Starter" | "$4,500+ Pro" | "$9,000+ Custom";
  deposit: string;
  message: string;
};

const SETUP_PACKAGE_EVENT = "wolfos:select-setup-package";

function selectSetupPackage(selection: SetupPackageSelection) {
  window.dispatchEvent(
    new CustomEvent<SetupPackageSelection>(SETUP_PACKAGE_EVENT, {
      detail: selection
    })
  );

  document.getElementById("request-setup-form")?.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });

  void trackAnalyticsEvent(
    "setup_package_select",
    `${selection.name}|${selection.budget}`
  );
}


function SetupRequestForm() {
'''

text = replace_once(
    text,
    setup_form_anchor,
    setup_package_bridge,
    "package selection bridge",
)


form_state_anchor = '''  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState("");
  const [formError, setFormError] = useState("");
'''

form_listener = '''  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState("");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    function handlePackageSelection(event: Event) {
      const selection = (
        event as CustomEvent<SetupPackageSelection>
      ).detail;

      if (!selection) {
        return;
      }

      setForm((current) => {
        const currentMessage = current.message.trim();
        const alreadyIncluded =
          currentMessage.includes(selection.name) ||
          currentMessage.includes(selection.budget);

        return {
          ...current,
          budget_range: selection.budget,
          message: alreadyIncluded
            ? current.message
            : currentMessage
              ? `${currentMessage}\\n\\n${selection.message}`
              : selection.message
        };
      });

      setFormError("");
      setSent(
        `${selection.name} selected. Starting deposit: ${selection.deposit}. Complete your contact details and send the request.`
      );
    }

    window.addEventListener(
      SETUP_PACKAGE_EVENT,
      handlePackageSelection
    );

    return () => {
      window.removeEventListener(
        SETUP_PACKAGE_EVENT,
        handlePackageSelection
      );
    };
  }, []);
'''

text = replace_once(
    text,
    form_state_anchor,
    form_listener,
    "setup-form package listener",
)

APP_PATH.write_text(text, encoding="utf-8", newline="\n")

print("Package conversion flow installed.")
print(f"Backup created: {backup_path}")
print(f"Updated: {APP_PATH}")
