import {
  useMemo,
  useState,
} from "react";

import {
  type PipelineState,
  useUnifiedPipeline,
} from "../lib/pipelineState";

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
    description:
      "Buyer-ready storefront, products, offers, and lead capture.",
  },
  {
    name:
      "Pro Storefront + Dashboard",
    price: 1500,
    description:
      "Storefront, owner dashboard, orders, inventory, leads, and analytics.",
  },
  {
    name:
      "Custom SaaS Buildout",
    price: 5000,
    description:
      "Custom workflows, automation, integrations, deployment, and support.",
  },
];

const money = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(
    Number.isFinite(value)
      ? value
      : 0
  );

function copyFallback(
  text: string
) {
  const textarea =
    document.createElement(
      "textarea"
    );

  textarea.value = text;
  textarea.style.position =
    "fixed";
  textarea.style.opacity = "0";

  document.body.appendChild(
    textarea
  );

  textarea.focus();
  textarea.select();

  document.execCommand("copy");

  document.body.removeChild(
    textarea
  );
}

export default function RevenueCommandCenter() {
  const {
    pipeline,
    pipelineStatus,
  } = useUnifiedPipeline();

  const [
    buyerBusiness,
    setBuyerBusiness,
  ] = useState("Next Buyer");

  const [
    monthlyGoal,
    setMonthlyGoal,
  ] = useState(10000);

  const [
    averageDeal,
    setAverageDeal,
  ] = useState(1500);

  const [
    selectedOffer,
    setSelectedOffer,
  ] = useState<Offer>(
    offers[1]
  );

  const [
    simulationRevenue,
    setSimulationRevenue,
  ] = useState(0);

  const [
    simulationCount,
    setSimulationCount,
  ] = useState(0);

  const [status, setStatus] =
    useState(
      "Revenue Engine connected to the unified SQLite pipeline."
    );

  const [
    copiedLabel,
    setCopiedLabel,
  ] = useState("");

  const pipelineDeals =
    Object.values(
      pipeline
    ) as PipelineState[];

  const activeDeals =
    pipelineDeals.filter(
      (deal) =>
        deal.stage !== "Won" &&
        deal.stage !== "Lost"
    );

  const wonDeals =
    pipelineDeals.filter(
      (deal) =>
        deal.stage === "Won"
    );

  const pipelineValue =
    activeDeals.reduce(
      (total, deal) =>
        total + deal.dealValue,
      0
    );

  const wonRevenue =
    wonDeals.reduce(
      (total, deal) =>
        total + deal.dealValue,
      0
    );

  const closedDeals =
    wonDeals.length;

  const securedRevenue =
    wonRevenue +
    simulationRevenue;

  const remainingRevenue =
    Math.max(
      0,
      monthlyGoal -
        securedRevenue
    );

  const dealsNeeded =
    averageDeal > 0
      ? Math.ceil(
          remainingRevenue /
            averageDeal
        )
      : 0;

  const progress =
    monthlyGoal > 0
      ? Math.min(
          100,
          Math.round(
            (
              securedRevenue /
              monthlyGoal
            ) * 100
          )
        )
      : 0;

  const pipelineCoverage =
    monthlyGoal > 0
      ? Math.round(
          (
            pipelineValue /
            monthlyGoal
          ) * 100
        )
      : 0;

  const salesPlan =
    useMemo(
      () =>
        [
          "WOLF OS™ REVENUE ATTACK PLAN",
          "",
          `Monthly revenue target: ${money(monthlyGoal)}`,
          `Won revenue: ${money(wonRevenue)}`,
          `Modeled revenue: ${money(simulationRevenue)}`,
          `Revenue secured: ${money(securedRevenue)}`,
          `Revenue remaining: ${money(remainingRevenue)}`,
          `Average deal target: ${money(averageDeal)}`,
          `Deals still needed: ${dealsNeeded}`,
          `Live SQLite pipeline: ${money(pipelineValue)}`,
          `Selected offer: ${selectedOffer.name} — ${money(selectedOffer.price)}`,
          "",
          "TONIGHT'S ACTIONS",
          "1. Execute the highest-priority WOLF OS target.",
          "2. Run the live demonstration.",
          "3. Move the deal through the Deal Desk.",
          "4. Send the recommended package.",
          "5. Ask for the deposit and launch date.",
        ].join("\n"),
      [
        monthlyGoal,
        wonRevenue,
        simulationRevenue,
        securedRevenue,
        remainingRevenue,
        averageDeal,
        dealsNeeded,
        pipelineValue,
        selectedOffer,
      ]
    );

  const closeScript =
    useMemo(
      () =>
        [
          `Hi ${buyerBusiness},`,
          "",
          "I built a live example of the kind of storefront and owner system your business could be operating.",
          "",
          `My recommended package is the ${selectedOffer.name} at ${money(selectedOffer.price)}+.`,
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
      [
        buyerBusiness,
        selectedOffer,
      ]
    );

  const copyText =
    async (
      text: string,
      label: string
    ) => {
      try {
        if (
          navigator.clipboard
            ?.writeText
        ) {
          await navigator.clipboard.writeText(
            text
          );
        } else {
          copyFallback(text);
        }

        setCopiedLabel(label);

        setStatus(
          `${label} copied and ready to use.`
        );

        window.setTimeout(
          () =>
            setCopiedLabel(""),
          1800
        );

      } catch {
        copyFallback(text);

        setCopiedLabel(label);

        setStatus(
          `${label} copied and ready to use.`
        );
      }
    };

  const runSimulation = () => {
    setSimulationRevenue(
      (current) =>
        current +
        selectedOffer.price
    );

    setSimulationCount(
      (current) =>
        current + 1
    );

    setStatus(
      `Sales simulation added ${selectedOffer.name}: ${money(selectedOffer.price)} in modeled revenue.`
    );
  };

  const openEmailDraft = () => {
    const subject =
      `${buyerBusiness} storefront + owner dashboard proposal`;

    window.location.href =
      `mailto:?subject=${encodeURIComponent(
        subject
      )}&body=${encodeURIComponent(
        closeScript
      )}`;

    setStatus(
      "Buyer email draft opened."
    );
  };

  return (
    <section className="revenue-command-center">
      <div className="revenue-command-glow" />

      <header className="revenue-command-header">
        <div>
          <p className="revenue-command-kicker">
            WOLF OS™ REVENUE ENGINE
          </p>

          <h2>
            Revenue Command Center
          </h2>

          <p>
            Live revenue intelligence
            calculated from the same SQLite
            pipeline used by Deal Desk and
            Priority Engine.
          </p>
        </div>

        <div className="revenue-command-status">
          <span className="revenue-status-light" />
          SQLITE REVENUE SYNC
        </div>
      </header>

      <div className="revenue-command-grid">
        <article className="revenue-gauge-card revenue-gauge-primary">
          <span>
            Monthly Goal
          </span>

          <strong>
            {money(monthlyGoal)}
          </strong>

          <div className="revenue-progress-track">
            <div
              className="revenue-progress-fill"
              style={{
                width:
                  `${progress}%`,
              }}
            />
          </div>

          <small>
            {progress}% secured
          </small>
        </article>

        <article className="revenue-gauge-card">
          <span>
            Revenue Secured
          </span>

          <strong>
            {money(
              securedRevenue
            )}
          </strong>

          <small>
            {closedDeals} won deal
            {closedDeals === 1
              ? ""
              : "s"}{" "}
            + {simulationCount} modeled
            simulation
            {simulationCount === 1
              ? ""
              : "s"}
          </small>
        </article>

        <article className="revenue-gauge-card">
          <span>
            Revenue Remaining
          </span>

          <strong>
            {money(
              remainingRevenue
            )}
          </strong>

          <small>
            {dealsNeeded} average
            deals required
          </small>
        </article>

        <article className="revenue-gauge-card">
          <span>
            Pipeline Coverage
          </span>

          <strong>
            {pipelineCoverage}%
          </strong>

          <small>
            {money(pipelineValue)} live
            SQLite pipeline
          </small>
        </article>
      </div>

      <div className="revenue-control-layout">
        <article className="revenue-control-panel">
          <div className="revenue-panel-heading">
            <div>
              <span>
                CONTROL BANK 01
              </span>

              <h3>
                Revenue Inputs
              </h3>
            </div>

            <b>
              SQLITE LIVE
            </b>
          </div>

          <div className="revenue-input-grid">
            <label>
              Buyer business

              <input
                value={
                  buyerBusiness
                }
                onChange={(event) =>
                  setBuyerBusiness(
                    event.target.value
                  )
                }
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
                  setMonthlyGoal(
                    Math.max(
                      0,
                      Number(
                        event.target
                          .value
                      ) || 0
                    )
                  )
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
                  setAverageDeal(
                    Math.max(
                      0,
                      Number(
                        event.target
                          .value
                      ) || 0
                    )
                  )
                }
              />
            </label>

            <label>
              Won deals from Deal Desk

              <input
                type="number"
                value={closedDeals}
                readOnly
              />
            </label>

            <label>
              Live pipeline from SQLite

              <input
                type="number"
                value={pipelineValue}
                readOnly
              />
            </label>
          </div>
        </article>

        <article className="revenue-control-panel">
          <div className="revenue-panel-heading">
            <div>
              <span>
                CONTROL BANK 02
              </span>

              <h3>
                Offer Selector
              </h3>
            </div>

            <b>
              {money(
                selectedOffer.price
              )}
            </b>
          </div>

          <div className="revenue-offer-stack">
            {offers.map(
              (offer) => (
                <button
                  type="button"
                  key={offer.name}
                  className={
                    selectedOffer.name ===
                    offer.name
                      ? "revenue-offer selected"
                      : "revenue-offer"
                  }
                  onClick={() => {
                    setSelectedOffer(
                      offer
                    );

                    setAverageDeal(
                      offer.price
                    );

                    setStatus(
                      `${offer.name} selected as the current closing offer.`
                    );
                  }}
                >
                  <span>
                    <strong>
                      {offer.name}
                    </strong>

                    <small>
                      {
                        offer.description
                      }
                    </small>
                  </span>

                  <b>
                    {money(
                      offer.price
                    )}
                    +
                  </b>
                </button>
              )
            )}
          </div>
        </article>
      </div>

      <div className="revenue-action-panel">
        <div>
          <span className="revenue-action-label">
            IGNITION CONTROLS
          </span>

          <h3>
            Turn pipeline action into
            secured revenue
          </h3>

          <p>
            {status}
            {" · "}
            {pipelineStatus}
          </p>
        </div>

        <div className="revenue-action-buttons">
          <button
            type="button"
            className="revenue-button revenue-button-primary"
            onClick={
              runSimulation
            }
          >
            Run Sales Simulation
          </button>

          <button
            type="button"
            className={
              copiedLabel ===
              "Revenue plan"
                ? "revenue-button copied"
                : "revenue-button"
            }
            onClick={() =>
              void copyText(
                salesPlan,
                "Revenue plan"
              )
            }
          >
            {copiedLabel ===
            "Revenue plan"
              ? "Revenue Plan Copied"
              : "Copy Revenue Plan"}
          </button>

          <button
            type="button"
            className={
              copiedLabel ===
              "Buyer close script"
                ? "revenue-button copied"
                : "revenue-button"
            }
            onClick={() =>
              void copyText(
                closeScript,
                "Buyer close script"
              )
            }
          >
            {copiedLabel ===
            "Buyer close script"
              ? "Close Script Copied"
              : "Copy Close Script"}
          </button>

          <button
            type="button"
            className="revenue-button"
            onClick={
              openEmailDraft
            }
          >
            Open Buyer Email
          </button>
        </div>
      </div>

      <footer className="revenue-command-footer">
        <span>
          Won revenue:{" "}
          <strong>
            {money(wonRevenue)}
          </strong>
        </span>

        <span>
          Active pipeline:{" "}
          <strong>
            {money(pipelineValue)}
          </strong>
        </span>

        <span>
          Deals to target:{" "}
          <strong>
            {dealsNeeded}
          </strong>
        </span>
      </footer>
    </section>
  );
}
