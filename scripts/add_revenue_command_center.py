from pathlib import Path
from datetime import datetime
import re
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"
COMPONENTS = SRC / "components"
APP = SRC / "App.tsx"

COMPONENT = COMPONENTS / "RevenueCommandCenter.tsx"
CSS = COMPONENTS / "RevenueCommandCenter.css"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Revenue Command Center patch starting...")

if not APP.exists():
    raise SystemExit(f"App.tsx not found: {APP}")

COMPONENTS.mkdir(parents=True, exist_ok=True)

backup = APP.with_name(f"App.before-revenue-engine-{stamp}.tsx")
shutil.copy2(APP, backup)
print(f"Backup created: {backup}")

component_code = r'''import { useMemo, useState } from "react";
import "./RevenueCommandCenter.css";

type Offer = {
  name: string;
  price: number;
  description: string;
};

const offers: Offer[] = [
  {
    name: "Starter Storefront",
    price: 499,
    description: "Buyer-ready storefront, products, offers, and lead capture.",
  },
  {
    name: "Pro Storefront + Dashboard",
    price: 1500,
    description: "Storefront, owner dashboard, orders, inventory, leads, and analytics.",
  },
  {
    name: "Custom SaaS Buildout",
    price: 5000,
    description: "Custom workflows, automation, integrations, deployment, and support.",
  },
];

const money = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(Number.isFinite(value) ? value : 0);

function copyFallback(text: string) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

export default function RevenueCommandCenter() {
  const [buyerBusiness, setBuyerBusiness] = useState("Next Buyer");
  const [monthlyGoal, setMonthlyGoal] = useState(10000);
  const [averageDeal, setAverageDeal] = useState(1500);
  const [closedDeals, setClosedDeals] = useState(0);
  const [pipelineValue, setPipelineValue] = useState(8500);
  const [selectedOffer, setSelectedOffer] = useState<Offer>(offers[1]);
  const [simulationRevenue, setSimulationRevenue] = useState(0);
  const [simulationCount, setSimulationCount] = useState(0);
  const [status, setStatus] = useState(
    "Revenue engine armed. Select an offer and run the sales simulation."
  );
  const [copiedLabel, setCopiedLabel] = useState("");

  const securedRevenue = closedDeals * averageDeal + simulationRevenue;
  const remainingRevenue = Math.max(0, monthlyGoal - securedRevenue);
  const dealsNeeded =
    averageDeal > 0 ? Math.ceil(remainingRevenue / averageDeal) : 0;
  const progress =
    monthlyGoal > 0
      ? Math.min(100, Math.round((securedRevenue / monthlyGoal) * 100))
      : 0;
  const pipelineCoverage =
    monthlyGoal > 0 ? Math.round((pipelineValue / monthlyGoal) * 100) : 0;

  const salesPlan = useMemo(
    () =>
      [
        "WOLF OS™ REVENUE ATTACK PLAN",
        "",
        `Monthly revenue target: ${money(monthlyGoal)}`,
        `Revenue secured: ${money(securedRevenue)}`,
        `Revenue remaining: ${money(remainingRevenue)}`,
        `Average deal target: ${money(averageDeal)}`,
        `Deals still needed: ${dealsNeeded}`,
        `Current pipeline: ${money(pipelineValue)}`,
        `Selected offer: ${selectedOffer.name} — ${money(selectedOffer.price)}`,
        "",
        "TONIGHT'S ACTIONS",
        "1. Contact qualified local businesses with an outdated or missing storefront.",
        "2. Lead with a live demonstration instead of a generic sales promise.",
        "3. Show the storefront, checkout flow, owner dashboard, leads, and analytics.",
        "4. Recommend one clear package based on the buyer's immediate needs.",
        "5. Ask for the deposit and define the launch date before ending the conversation.",
      ].join("\n"),
    [
      monthlyGoal,
      securedRevenue,
      remainingRevenue,
      averageDeal,
      dealsNeeded,
      pipelineValue,
      selectedOffer,
    ]
  );

  const closeScript = useMemo(
    () =>
      [
        `Hi ${buyerBusiness},`,
        "",
        "I built a live example of the kind of storefront and owner system your business could be operating.",
        "",
        `My recommended package is the ${selectedOffer.name} at ${money(
          selectedOffer.price
        )}+.`,
        "",
        selectedOffer.description,
        "",
        "The system can give you:",
        "• A professional buyer-facing storefront",
        "• Products, services, or package presentation",
        "• Checkout or lead-request workflow",
        "• An owner command dashboard",
        "• Order, inventory, and lead visibility",
        "• A structure that can be customized and launched quickly",
        "",
        "The next step is confirming your exact content, features, payment structure, and launch timeline.",
        "",
        "Would you like to move forward with the setup deposit?",
        "",
        "Andrew Wolverton",
        "I AM THE ONE™ · WOLF OS™",
      ].join("\n"),
    [buyerBusiness, selectedOffer]
  );

  const copyText = async (text: string, label: string) => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        copyFallback(text);
      }

      setCopiedLabel(label);
      setStatus(`${label} copied and ready to use.`);

      window.setTimeout(() => {
        setCopiedLabel("");
      }, 1800);
    } catch {
      copyFallback(text);
      setCopiedLabel(label);
      setStatus(`${label} copied and ready to use.`);
    }
  };

  const runSimulation = () => {
    setSimulationRevenue((current) => current + selectedOffer.price);
    setSimulationCount((current) => current + 1);
    setStatus(
      `Sales simulation added ${selectedOffer.name}: ${money(
        selectedOffer.price
      )} in modeled revenue.`
    );
  };

  const openEmailDraft = () => {
    const subject = `${buyerBusiness} storefront + owner dashboard proposal`;
    window.location.href = `mailto:?subject=${encodeURIComponent(
      subject
    )}&body=${encodeURIComponent(closeScript)}`;
    setStatus("Buyer email draft opened in your configured email application.");
  };

  return (
    <section className="revenue-command-center">
      <div className="revenue-command-glow" />

      <header className="revenue-command-header">
        <div>
          <p className="revenue-command-kicker">
            WOLF OS™ REVENUE ENGINE
          </p>
          <h2>Revenue Command Center</h2>
          <p>
            Convert the working SaaS demo into clear offers, sales activity,
            deposits, and measurable revenue targets.
          </p>
        </div>

        <div className="revenue-command-status">
          <span className="revenue-status-light" />
          SALES SYSTEM ARMED
        </div>
      </header>

      <div className="revenue-command-grid">
        <article className="revenue-gauge-card revenue-gauge-primary">
          <span>Monthly Goal</span>
          <strong>{money(monthlyGoal)}</strong>

          <div className="revenue-progress-track">
            <div
              className="revenue-progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>

          <small>{progress}% modeled progress</small>
        </article>

        <article className="revenue-gauge-card">
          <span>Revenue Secured</span>
          <strong>{money(securedRevenue)}</strong>
          <small>
            {closedDeals} actual deal{closedDeals === 1 ? "" : "s"} +{" "}
            {simulationCount} simulation
            {simulationCount === 1 ? "" : "s"}
          </small>
        </article>

        <article className="revenue-gauge-card">
          <span>Revenue Remaining</span>
          <strong>{money(remainingRevenue)}</strong>
          <small>{dealsNeeded} average deals required</small>
        </article>

        <article className="revenue-gauge-card">
          <span>Pipeline Coverage</span>
          <strong>{pipelineCoverage}%</strong>
          <small>{money(pipelineValue)} active pipeline</small>
        </article>
      </div>

      <div className="revenue-control-layout">
        <article className="revenue-control-panel">
          <div className="revenue-panel-heading">
            <div>
              <span>CONTROL BANK 01</span>
              <h3>Revenue Inputs</h3>
            </div>
            <b>LIVE</b>
          </div>

          <div className="revenue-input-grid">
            <label>
              Buyer business
              <input
                value={buyerBusiness}
                onChange={(event) => setBuyerBusiness(event.target.value)}
                placeholder="Buyer business name"
              />
            </label>

            <label>
              Monthly revenue goal
              <input
                type="number"
                min="0"
                step="500"
                value={monthlyGoal}
                onChange={(event) =>
                  setMonthlyGoal(Math.max(0, Number(event.target.value) || 0))
                }
              />
            </label>

            <label>
              Average deal value
              <input
                type="number"
                min="0"
                step="100"
                value={averageDeal}
                onChange={(event) =>
                  setAverageDeal(Math.max(0, Number(event.target.value) || 0))
                }
              />
            </label>

            <label>
              Closed deals
              <input
                type="number"
                min="0"
                step="1"
                value={closedDeals}
                onChange={(event) =>
                  setClosedDeals(Math.max(0, Number(event.target.value) || 0))
                }
              />
            </label>

            <label>
              Active pipeline value
              <input
                type="number"
                min="0"
                step="500"
                value={pipelineValue}
                onChange={(event) =>
                  setPipelineValue(Math.max(0, Number(event.target.value) || 0))
                }
              />
            </label>
          </div>
        </article>

        <article className="revenue-control-panel">
          <div className="revenue-panel-heading">
            <div>
              <span>CONTROL BANK 02</span>
              <h3>Offer Selector</h3>
            </div>
            <b>{money(selectedOffer.price)}</b>
          </div>

          <div className="revenue-offer-stack">
            {offers.map((offer) => (
              <button
                type="button"
                key={offer.name}
                className={
                  selectedOffer.name === offer.name
                    ? "revenue-offer selected"
                    : "revenue-offer"
                }
                onClick={() => {
                  setSelectedOffer(offer);
                  setAverageDeal(offer.price);
                  setStatus(
                    `${offer.name} selected as the current closing offer.`
                  );
                }}
              >
                <span>
                  <strong>{offer.name}</strong>
                  <small>{offer.description}</small>
                </span>
                <b>{money(offer.price)}+</b>
              </button>
            ))}
          </div>
        </article>
      </div>

      <div className="revenue-action-panel">
        <div>
          <span className="revenue-action-label">IGNITION CONTROLS</span>
          <h3>Turn the demo into a buyer conversation</h3>
          <p>{status}</p>
        </div>

        <div className="revenue-action-buttons">
          <button
            type="button"
            className="revenue-button revenue-button-primary"
            onClick={runSimulation}
          >
            Run Sales Simulation
          </button>

          <button
            type="button"
            className={copiedLabel === "Revenue plan" ? "revenue-button copied" : "revenue-button"}
            onClick={() => copyText(salesPlan, "Revenue plan")}
          >
            {copiedLabel === "Revenue plan"
              ? "Revenue Plan Copied"
              : "Copy Revenue Plan"}
          </button>

          <button
            type="button"
            className={copiedLabel === "Buyer close script" ? "revenue-button copied" : "revenue-button"}
            onClick={() => copyText(closeScript, "Buyer close script")}
          >
            {copiedLabel === "Buyer close script"
              ? "Close Script Copied"
              : "Copy Close Script"}
          </button>

          <button
            type="button"
            className="revenue-button"
            onClick={openEmailDraft}
          >
            Open Buyer Email
          </button>
        </div>
      </div>

      <footer className="revenue-command-footer">
        <span>
          Selected offer: <strong>{selectedOffer.name}</strong>
        </span>
        <span>
          Target deal value: <strong>{money(selectedOffer.price)}</strong>
        </span>
        <span>
          Deals to target: <strong>{dealsNeeded}</strong>
        </span>
      </footer>
    </section>
  );
}
'''

css_code = r'''.revenue-command-center {
  position: relative;
  overflow: hidden;
  margin-top: 28px;
  padding: 26px;
  border: 1px solid rgba(255, 174, 0, 0.34);
  border-radius: 24px;
  background:
    radial-gradient(circle at 85% 5%, rgba(255, 119, 0, 0.13), transparent 30%),
    linear-gradient(145deg, rgba(12, 14, 18, 0.98), rgba(3, 4, 7, 0.98));
  box-shadow:
    0 24px 70px rgba(0, 0, 0, 0.48),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.revenue-command-center * {
  box-sizing: border-box;
}

.revenue-command-glow {
  position: absolute;
  top: -140px;
  right: -80px;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  background: rgba(255, 111, 0, 0.12);
  filter: blur(80px);
  pointer-events: none;
}

.revenue-command-header,
.revenue-panel-heading,
.revenue-command-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.revenue-command-header {
  position: relative;
  margin-bottom: 22px;
}

.revenue-command-kicker,
.revenue-panel-heading span,
.revenue-action-label {
  display: block;
  margin: 0 0 7px;
  color: #ffad32;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.17em;
  text-transform: uppercase;
}

.revenue-command-header h2,
.revenue-control-panel h3,
.revenue-action-panel h3 {
  margin: 0;
  color: #ffffff;
}

.revenue-command-header h2 {
  font-size: clamp(1.55rem, 3vw, 2.4rem);
  letter-spacing: -0.04em;
}

.revenue-command-header p,
.revenue-action-panel p {
  max-width: 760px;
  margin: 9px 0 0;
  color: rgba(237, 242, 249, 0.68);
  line-height: 1.6;
}

.revenue-command-status {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 9px;
  padding: 10px 13px;
  border: 1px solid rgba(80, 255, 168, 0.27);
  border-radius: 999px;
  background: rgba(17, 84, 54, 0.16);
  color: #72ffb2;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.revenue-status-light {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #57ff9d;
  box-shadow: 0 0 16px #57ff9d;
}

.revenue-command-grid {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 13px;
}

.revenue-gauge-card {
  min-height: 145px;
  padding: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  background:
    linear-gradient(150deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.012));
}

.revenue-gauge-primary {
  border-color: rgba(255, 169, 42, 0.35);
  background:
    linear-gradient(150deg, rgba(255, 137, 0, 0.16), rgba(255, 255, 255, 0.014));
}

.revenue-gauge-card > span {
  color: rgba(238, 243, 250, 0.58);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.revenue-gauge-card > strong {
  display: block;
  margin-top: 14px;
  color: #ffffff;
  font-size: clamp(1.45rem, 2.7vw, 2.25rem);
  letter-spacing: -0.04em;
}

.revenue-gauge-card small {
  display: block;
  margin-top: 12px;
  color: rgba(228, 235, 244, 0.55);
  line-height: 1.4;
}

.revenue-progress-track {
  height: 7px;
  margin-top: 17px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.revenue-progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #ff7800, #ffcf55);
  box-shadow: 0 0 16px rgba(255, 150, 0, 0.5);
  transition: width 280ms ease;
}

.revenue-control-layout {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 15px;
  margin-top: 15px;
}

.revenue-control-panel,
.revenue-action-panel {
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.075);
  border-radius: 19px;
  background: rgba(255, 255, 255, 0.025);
}

.revenue-panel-heading {
  margin-bottom: 17px;
}

.revenue-panel-heading h3 {
  font-size: 1.05rem;
}

.revenue-panel-heading b {
  color: #ffbc4c;
  font-size: 0.83rem;
}

.revenue-input-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.revenue-input-grid label:first-child {
  grid-column: 1 / -1;
}

.revenue-input-grid label {
  color: rgba(233, 239, 247, 0.62);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.03em;
}

.revenue-input-grid input {
  width: 100%;
  margin-top: 7px;
  padding: 12px 13px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 11px;
  outline: none;
  background: rgba(0, 0, 0, 0.27);
  color: #ffffff;
  font: inherit;
  font-size: 0.93rem;
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease;
}

.revenue-input-grid input:focus {
  border-color: rgba(255, 168, 41, 0.65);
  box-shadow: 0 0 0 3px rgba(255, 142, 0, 0.1);
}

.revenue-offer-stack {
  display: grid;
  gap: 10px;
}

.revenue-offer {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  padding: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.025);
  color: #ffffff;
  text-align: left;
  cursor: pointer;
  transition:
    transform 150ms ease,
    border-color 150ms ease,
    background 150ms ease;
}

.revenue-offer:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 178, 56, 0.35);
}

.revenue-offer.selected {
  border-color: rgba(255, 172, 44, 0.65);
  background:
    linear-gradient(120deg, rgba(255, 125, 0, 0.18), rgba(255, 196, 71, 0.05));
  box-shadow: inset 3px 0 0 #ff9d21;
}

.revenue-offer span {
  min-width: 0;
}

.revenue-offer strong,
.revenue-offer small {
  display: block;
}

.revenue-offer strong {
  font-size: 0.88rem;
}

.revenue-offer small {
  margin-top: 5px;
  color: rgba(231, 237, 245, 0.5);
  font-size: 0.72rem;
  line-height: 1.4;
}

.revenue-offer b {
  flex-shrink: 0;
  color: #ffc25c;
}

.revenue-action-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 25px;
  margin-top: 15px;
  border-color: rgba(255, 168, 34, 0.18);
}

.revenue-action-panel h3 {
  font-size: 1.15rem;
}

.revenue-action-panel p {
  max-width: 610px;
  font-size: 0.85rem;
}

.revenue-action-buttons {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 9px;
}

.revenue-button {
  padding: 11px 14px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.055);
  color: #ffffff;
  font-size: 0.77rem;
  font-weight: 900;
  cursor: pointer;
  transition:
    transform 150ms ease,
    border-color 150ms ease,
    background 150ms ease;
}

.revenue-button:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 184, 68, 0.45);
}

.revenue-button-primary {
  border-color: #ff9e24;
  background: linear-gradient(135deg, #ff7200, #ffb629);
  color: #130900;
  box-shadow: 0 10px 30px rgba(255, 119, 0, 0.22);
}

.revenue-button.copied {
  border-color: rgba(82, 255, 168, 0.55);
  background: rgba(39, 151, 94, 0.19);
  color: #78ffb7;
}

.revenue-command-footer {
  margin-top: 15px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.23);
  color: rgba(228, 235, 244, 0.57);
  font-size: 0.77rem;
}

.revenue-command-footer strong {
  color: #ffffff;
}

@media (max-width: 1050px) {
  .revenue-command-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .revenue-control-layout {
    grid-template-columns: 1fr;
  }

  .revenue-action-panel {
    align-items: flex-start;
    flex-direction: column;
  }

  .revenue-action-buttons {
    justify-content: flex-start;
  }
}

@media (max-width: 680px) {
  .revenue-command-center {
    padding: 18px;
    border-radius: 19px;
  }

  .revenue-command-header,
  .revenue-command-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .revenue-command-grid,
  .revenue-input-grid {
    grid-template-columns: 1fr;
  }

  .revenue-input-grid label:first-child {
    grid-column: auto;
  }

  .revenue-command-status {
    align-self: flex-start;
  }

  .revenue-action-buttons,
  .revenue-button {
    width: 100%;
  }

  .revenue-command-footer {
    gap: 8px;
  }
}
'''

COMPONENT.write_text(component_code, encoding="utf-8")
CSS.write_text(css_code, encoding="utf-8")

print(f"Created: {COMPONENT}")
print(f"Created: {CSS}")

app_text = APP.read_text(encoding="utf-8")

import_line = 'import RevenueCommandCenter from "./components/RevenueCommandCenter";'

if import_line not in app_text:
    insertion_match = re.search(
        r"(?m)^(type|interface|const|function|export)\b",
        app_text,
    )

    if insertion_match:
        position = insertion_match.start()
        app_text = (
            app_text[:position]
            + import_line
            + "\n\n"
            + app_text[position:]
        )
    else:
        app_text = import_line + "\n" + app_text

    print("Added RevenueCommandCenter import.")
else:
    print("RevenueCommandCenter import already exists.")

if "<RevenueCommandCenter" not in app_text:
    panel_match = re.search(
        r"<BusinessIntelligencePanel\b[\s\S]*?/>",
        app_text,
    )

    if panel_match is None:
        panel_match = re.search(
            r"<BusinessIntelligencePanel\b[\s\S]*?</BusinessIntelligencePanel>",
            app_text,
        )

    if panel_match is None:
        raise SystemExit(
            "Could not locate the BusinessIntelligencePanel component call. "
            "App.tsx was backed up and the new component files were created, "
            "but App.tsx was not changed."
        )

    line_start = app_text.rfind("\n", 0, panel_match.start()) + 1
    indentation_match = re.match(
        r"[ \t]*",
        app_text[line_start:panel_match.start()],
    )
    indentation = indentation_match.group(0) if indentation_match else ""

    insert_position = panel_match.end()

    app_text = (
        app_text[:insert_position]
        + "\n"
        + indentation
        + "<RevenueCommandCenter />"
        + app_text[insert_position:]
    )

    print("Inserted Revenue Command Center beneath Business Intelligence.")
else:
    print("Revenue Command Center is already inserted.")

APP.write_text(app_text, encoding="utf-8")

print()
print("Running frontend build...")

npm_command = "npm.cmd" if sys.platform.startswith("win") else "npm"

result = subprocess.run(
    [npm_command, "run", "build"],
    cwd=FRONTEND,
    text=True,
)

if result.returncode != 0:
    raise SystemExit(
        "Frontend build failed. Review the TypeScript error above. "
        f"Your App.tsx backup is: {backup}"
    )

print()
print("SUCCESS: Revenue Command Center installed and frontend build passed.")
print("Open the Owner Console and test:")
print("1. Select a package.")
print("2. Change the monthly revenue goal.")
print("3. Run Sales Simulation.")
print("4. Copy Revenue Plan.")
print("5. Copy Close Script.")
print("6. Open Buyer Email.")
