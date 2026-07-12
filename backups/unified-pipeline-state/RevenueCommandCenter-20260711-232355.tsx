import { useMemo, useState } from "react";
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
