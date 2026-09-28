import { useMemo, useState } from "react";

import "./OwnerActionEngine.css";


type Props = {
  orders: unknown[];
  products: unknown[];
  setupRequests: unknown[];
};


type ActionSignal = {
  id: string;
  score: number;
  level: "critical" | "high" | "medium" | "clear";
  label: string;
  headline: string;
  detail: string;
  metric: string;
  button: string;
  selector: string;
};


function asRecord(
  value: unknown
): Record<string, unknown> {
  if (
    value &&
    typeof value === "object" &&
    !Array.isArray(value)
  ) {
    return value as Record<string, unknown>;
  }

  return {};
}


function textValue(
  record: Record<string, unknown>,
  keys: string[]
): string {
  for (const key of keys) {
    const value = record[key];

    if (
      typeof value === "string" &&
      value.trim()
    ) {
      return value.trim();
    }
  }

  return "";
}


function numberValue(
  record: Record<string, unknown>,
  keys: string[]
): number {
  for (const key of keys) {
    const value = Number(record[key]);

    if (Number.isFinite(value)) {
      return value;
    }
  }

  return 0;
}


function moneyFromCents(
  cents: number
): string {
  return new Intl.NumberFormat(
    "en-US",
    {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }
  ).format(
    Math.max(0, cents) / 100
  );
}


export default function OwnerActionEngine({
  orders,
  products,
  setupRequests,
}: Props) {
  const [status, setStatus] = useState(
    "WOLF OS is analyzing live owner conditions."
  );

  const intelligence = useMemo(() => {
    const orderRows = orders.map(asRecord);
    const productRows = products.map(asRecord);
    const leadRows = setupRequests.map(asRecord);

    let outstandingCents = 0;
    let unpaidOrders = 0;

    for (const order of orderRows) {
      const paymentStatus = textValue(
        order,
        [
          "payment_status",
          "paymentStatus",
          "status",
        ]
      ).toLowerCase();

      if (
        paymentStatus === "paid" ||
        paymentStatus === "refunded" ||
        paymentStatus === "cancelled"
      ) {
        continue;
      }

      const totalCents = numberValue(
        order,
        [
          "total_cents",
          "totalCents",
        ]
      );

      const amountPaidCents = numberValue(
        order,
        [
          "amount_paid_cents",
          "amountPaidCents",
        ]
      );

      const openBalance = Math.max(
        0,
        totalCents - amountPaidCents
      );

      if (openBalance > 0) {
        unpaidOrders += 1;
        outstandingCents += openBalance;
      }
    }

    const outOfStock = productRows.filter(
      (product) =>
        numberValue(
          product,
          ["stock", "inventory"]
        ) <= 0
    );

    const lowStock = productRows.filter(
      (product) => {
        const stock = numberValue(
          product,
          ["stock", "inventory"]
        );

        return stock > 0 && stock <= 3;
      }
    );

    const activeLeads = leadRows.filter(
      (lead) => {
        const statusValue = textValue(
          lead,
          [
            "status",
            "stage",
          ]
        ).toLowerCase();

        return ![
          "won",
          "lost",
          "closed",
          "cancelled",
        ].includes(statusValue);
      }
    );

    const firstLead = activeLeads[0]
      ? textValue(
          activeLeads[0],
          [
            "business_name",
            "business",
            "company",
            "store_name",
            "name",
          ]
        )
      : "";

    const signals: ActionSignal[] = [];

    if (outstandingCents > 0) {
      signals.push({
        id: "collections",
        score:
          130 +
          Math.min(
            40,
            Math.round(
              outstandingCents / 10000
            )
          ),
        level: "critical",
        label: "REVENUE WAITING",
        headline:
          `${moneyFromCents(
            outstandingCents
          )} is still collectible`,
        detail:
          `${unpaidOrders} order${
            unpaidOrders === 1 ? "" : "s"
          } still ${
            unpaidOrders === 1
              ? "requires"
              : "require"
          } payment action.`,
        metric: moneyFromCents(
          outstandingCents
        ),
        button: "OPEN REVENUE ENGINE",
        selector: ".revenue-command-center",
      });
    }

    if (outOfStock.length > 0) {
      signals.push({
        id: "out-of-stock",
        score:
          120 +
          outOfStock.length * 5,
        level: "critical",
        label: "INVENTORY STOP",
        headline:
          `${outOfStock.length} product${
            outOfStock.length === 1
              ? " is"
              : "s are"
          } out of stock`,
        detail:
          "Buyer flow can be interrupted until inventory is restored.",
        metric: `${outOfStock.length} OUT`,
        button: "VIEW INVENTORY",
        selector: ".metric-grid",
      });
    }

    if (activeLeads.length > 0) {
      signals.push({
        id: "buyers",
        score:
          95 +
          Math.min(
            25,
            activeLeads.length * 4
          ),
        level: "high",
        label: "BUYER ACTION",
        headline:
          `${activeLeads.length} active buyer${
            activeLeads.length === 1
              ? ""
              : "s"
          } need attention`,
        detail: firstLead
          ? `${firstLead} is currently at the front of the opportunity queue.`
          : "The Priority Engine has active revenue opportunities waiting.",
        metric: `${activeLeads.length} ACTIVE`,
        button: "OPEN PRIORITY ENGINE",
        selector: ".priority-engine",
      });
    }

    if (lowStock.length > 0) {
      signals.push({
        id: "low-stock",
        score:
          70 +
          lowStock.length * 3,
        level: "medium",
        label: "STOCK WARNING",
        headline:
          `${lowStock.length} product${
            lowStock.length === 1
              ? " is"
              : "s are"
          } running low`,
        detail:
          "Inventory is still sellable, but replenishment should be planned.",
        metric: `${lowStock.length} LOW`,
        button: "VIEW INVENTORY",
        selector: ".metric-grid",
      });
    }

    if (signals.length === 0) {
      signals.push({
        id: "clear",
        score: 0,
        level: "clear",
        label: "SYSTEM CLEAR",
        headline:
          "No urgent owner action detected",
        detail:
          "Revenue, buyer activity, and inventory are currently inside normal operating ranges.",
        metric: "CLEAR",
        button: "OPEN PRIORITY ENGINE",
        selector: ".priority-engine",
      });
    }

    signals.sort(
      (a, b) => b.score - a.score
    );

    return {
      signals,
      primary: signals[0],
      outstandingCents,
      unpaidOrders,
      outOfStockCount:
        outOfStock.length,
      lowStockCount:
        lowStock.length,
      activeLeadCount:
        activeLeads.length,
    };
  }, [
    orders,
    products,
    setupRequests,
  ]);


  const executeFocus = (
    signal: ActionSignal
  ) => {
    const target =
      document.querySelector(
        signal.selector
      );

    if (
      target instanceof HTMLElement
    ) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });

      setStatus(
        `${signal.label}: focus moved to the operating panel.`
      );

      return;
    }

    setStatus(
      `${signal.label}: operating panel is not currently visible.`
    );
  };


  const copyAction = async () => {
    const signal = intelligence.primary;

    const plan = [
      "WOLF OS? NEXT BEST ACTION",
      "",
      signal.label,
      signal.headline,
      signal.detail,
      "",
      `Priority score: ${signal.score}`,
      `Open revenue: ${moneyFromCents(
        intelligence.outstandingCents
      )}`,
      `Unpaid orders: ${intelligence.unpaidOrders}`,
      `Active buyers: ${intelligence.activeLeadCount}`,
      `Out of stock: ${intelligence.outOfStockCount}`,
      `Low stock: ${intelligence.lowStockCount}`,
    ].join("\n");

    try {
      await navigator.clipboard.writeText(
        plan
      );

      setStatus(
        "Next Best Action copied."
      );
    } catch {
      setStatus(
        "Clipboard unavailable. Action remains visible on screen."
      );
    }
  };


  const primary =
    intelligence.primary;

  return (
    <section
      className={`owner-action-engine action-${primary.level}`}
    >
      <div className="owner-action-scan" />

      <header className="owner-action-header">
        <div>
          <p className="owner-action-kicker">
            WOLF OS? OWNER ACTION ENGINE
          </p>

          <h2>
            Next Best Action
          </h2>

          <p className="owner-action-subtitle">
            Live orders, buyers, and inventory
            ranked into one owner directive.
          </p>
        </div>

        <div className="owner-action-live">
          <span />
          DECISION ENGINE LIVE
        </div>
      </header>

      <div className="owner-action-layout">
        <article className="owner-action-primary">
          <div className="owner-action-priority-row">
            <span
              className={`owner-action-level ${primary.level}`}
            >
              {primary.label}
            </span>

            <span className="owner-action-score">
              SCORE {primary.score}
            </span>
          </div>

          <div className="owner-action-metric">
            {primary.metric}
          </div>

          <h3>
            {primary.headline}
          </h3>

          <p>
            {primary.detail}
          </p>

          <div className="owner-action-buttons">
            <button
              type="button"
              className="owner-action-button primary"
              onClick={() =>
                executeFocus(primary)
              }
            >
              {primary.button}
            </button>

            <button
              type="button"
              className="owner-action-button"
              onClick={copyAction}
            >
              COPY ACTION
            </button>
          </div>
        </article>

        <aside className="owner-action-side">
          <div className="owner-action-stat">
            <span>OPEN CASH</span>
            <strong>
              {moneyFromCents(
                intelligence.outstandingCents
              )}
            </strong>
          </div>

          <div className="owner-action-stat">
            <span>ACTIVE BUYERS</span>
            <strong>
              {intelligence.activeLeadCount}
            </strong>
          </div>

          <div className="owner-action-stat">
            <span>STOCK RISK</span>
            <strong>
              {intelligence.outOfStockCount +
                intelligence.lowStockCount}
            </strong>
          </div>
        </aside>
      </div>

      {intelligence.signals.length > 1 && (
        <div className="owner-action-secondary">
          {intelligence.signals
            .slice(1, 4)
            .map((signal) => (
              <button
                type="button"
                key={signal.id}
                className="owner-action-secondary-card"
                onClick={() =>
                  executeFocus(signal)
                }
              >
                <span>
                  {signal.label}
                </span>

                <strong>
                  {signal.headline}
                </strong>

                <small>
                  {signal.detail}
                </small>
              </button>
            ))}
        </div>
      )}

      <footer className="owner-action-footer">
        <span className="owner-action-footer-light" />
        {status}
      </footer>
    </section>
  );
}
