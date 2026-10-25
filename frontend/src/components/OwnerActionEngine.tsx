import { useMemo, useState } from "react";

import { useUnifiedPipeline } from "../lib/pipelineState";

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
  revenueCents: number;
  urgency: number;
  probability: number;
  nextMove: string;
};


type ActionCandidate = Omit<
  ActionSignal,
  "score" | "level"
>;


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

    if (
      typeof value === "number" &&
      Number.isFinite(value)
    ) {
      return String(value);
    }
  }

  return "";
}


function parseNumber(
  value: unknown
): number {
  if (typeof value === "number") {
    return Number.isFinite(value)
      ? value
      : 0;
  }

  if (typeof value !== "string") {
    return 0;
  }

  const match = value.match(
    /-?\$?([\d,]+(?:\.\d+)?)/
  );

  if (!match) {
    return 0;
  }

  const number = Number(
    match[1].replace(/,/g, "")
  );

  return Number.isFinite(number)
    ? number
    : 0;
}


function numberValue(
  record: Record<string, unknown>,
  keys: string[]
): number {
  for (const key of keys) {
    const value = parseNumber(record[key]);

    if (value !== 0) {
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


function clamp(
  value: number,
  min: number,
  max: number
): number {
  return Math.min(
    max,
    Math.max(min, value)
  );
}


function leadValueCents(
  lead: Record<string, unknown>
): number {
  const directCents = numberValue(
    lead,
    [
      "budget_cents",
      "estimated_value_cents",
      "deal_value_cents",
      "value_cents",
      "amount_cents",
    ]
  );

  if (directCents > 0) {
    return Math.round(directCents);
  }

  const dollars = numberValue(
    lead,
    [
      "budget",
      "budget_amount",
      "estimated_value",
      "deal_value",
      "value",
    ]
  );

  if (dollars > 0) {
    return Math.round(
      dollars * 100
    );
  }

  return 0;
}


function leadProbability(
  lead: Record<string, unknown>
): number {
  const stage = textValue(
    lead,
    [
      "stage",
      "status",
      "pipeline_stage",
    ]
  ).toLowerCase();

  if (
    stage.includes("negotiat") ||
    stage.includes("closing")
  ) {
    return 85;
  }

  if (
    stage.includes("proposal") ||
    stage.includes("quote")
  ) {
    return 72;
  }

  if (
    stage.includes("qualified") ||
    stage.includes("hot")
  ) {
    return 58;
  }

  if (
    stage.includes("contact") ||
    stage.includes("follow")
  ) {
    return 45;
  }

  if (
    stage.includes("new") ||
    !stage
  ) {
    return 30;
  }

  return 38;
}


function leadUrgency(
  lead: Record<string, unknown>
): number {
  const timeline = textValue(
    lead,
    [
      "timeline",
      "timeframe",
      "urgency",
    ]
  ).toLowerCase();

  const stage = textValue(
    lead,
    [
      "stage",
      "status",
      "pipeline_stage",
    ]
  ).toLowerCase();

  let urgency = 45;

  if (
    timeline.includes("asap") ||
    timeline.includes("urgent") ||
    timeline.includes("immediate") ||
    timeline.includes("now")
  ) {
    urgency = 100;
  } else if (
    timeline.includes("week")
  ) {
    urgency = 88;
  } else if (
    timeline.includes("30") ||
    timeline.includes("month")
  ) {
    urgency = 72;
  } else if (
    timeline.includes("quarter") ||
    timeline.includes("90")
  ) {
    urgency = 52;
  }

  if (
    stage.includes("proposal") ||
    stage.includes("quote")
  ) {
    urgency += 10;
  }

  if (
    stage.includes("negotiat") ||
    stage.includes("closing")
  ) {
    urgency += 15;
  }

  const createdText = textValue(
    lead,
    [
      "created_at",
      "createdAt",
      "updated_at",
      "updatedAt",
    ]
  );

  if (createdText) {
    const created = new Date(createdText);

    if (!Number.isNaN(created.getTime())) {
      const ageDays =
        (
          Date.now() -
          created.getTime()
        ) /
        86400000;

      if (ageDays >= 7) {
        urgency += 12;
      } else if (ageDays >= 3) {
        urgency += 6;
      }
    }
  }

  return clamp(
    Math.round(urgency),
    0,
    100
  );
}


function leadNextMove(
  lead: Record<string, unknown>
): string {
  const stage = textValue(
    lead,
    [
      "stage",
      "status",
      "pipeline_stage",
    ]
  ).toLowerCase();

  if (
    stage.includes("negotiat") ||
    stage.includes("closing")
  ) {
    return "Ask for commitment and lock the payment or launch terms.";
  }

  if (
    stage.includes("proposal") ||
    stage.includes("quote")
  ) {
    return "Send the proposal follow-up and ask for a decision.";
  }

  if (
    stage.includes("qualified") ||
    stage.includes("hot")
  ) {
    return "Send the tailored offer and move the buyer into proposal.";
  }

  if (
    stage.includes("contact") ||
    stage.includes("follow")
  ) {
    return "Follow up now and confirm budget, timeline, and next step.";
  }

  return "Contact the buyer and qualify budget, timeline, and buying intent.";
}


function levelForScore(
  score: number
): ActionSignal["level"] {
  if (score >= 80) {
    return "critical";
  }

  if (score >= 64) {
    return "high";
  }

  if (score >= 42) {
    return "medium";
  }

  return "clear";
}


function ownerActionPipelineKey(
  lead: Record<string, unknown>,
  index: number
): string {
  const business =
    textValue(
      lead,
      [
        "business_name",
        "businessName",
        "business",
      ]
    ) ||
    `Buyer Lead ${index + 1}`;

  const name =
    textValue(
      lead,
      [
        "name",
        "contact_name",
        "contactName",
      ]
    ) ||
    "Buyer";

  const email =
    textValue(
      lead,
      ["email"]
    );

  const id =
    textValue(
      lead,
      [
        "id",
        "request_id",
        "created_at",
      ]
    );

  return (
    id ||
    `${business}-${email || name}-${index}`
  );
}


export default function OwnerActionEngine({
  orders,
  products,
  setupRequests,
}: Props) {
  const { pipeline } = useUnifiedPipeline();
  const [status, setStatus] = useState(
    "WOLF OS is analyzing revenue impact, urgency, and probability."
  );


  const intelligence = useMemo(() => {
    const orderRows =
      orders.map(asRecord);

    const productRows =
      products.map(asRecord);

    const leadRows =
      setupRequests.map(asRecord);


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

      const amountPaidCents =
        numberValue(
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


    const outOfStock =
      productRows.filter(
        (product) =>
          numberValue(
            product,
            ["stock", "inventory"]
          ) <= 0
      );


    const lowStock =
      productRows.filter(
        (product) => {
          const stock = numberValue(
            product,
            ["stock", "inventory"]
          );

          return stock > 0 && stock <= 3;
        }
      );


    const outOfStockRiskCents =
      outOfStock.reduce(
        (sum, product) =>
          sum +
          Math.max(
            0,
            numberValue(
              product,
              [
                "price_cents",
                "priceCents",
              ]
            )
          ),
        0
      );


    const lowStockRiskCents =
      lowStock.reduce(
        (sum, product) =>
          sum +
          Math.max(
            0,
            numberValue(
              product,
              [
                "price_cents",
                "priceCents",
              ]
            )
          ),
        0
      );


    const activeLeads =
      leadRows.filter(
        (lead) => {
          const value = textValue(
            lead,
            [
              "status",
              "stage",
              "pipeline_stage",
            ]
          ).toLowerCase();

          return ![
            "won",
            "lost",
            "closed",
            "cancelled",
            "canceled",
          ].includes(value);
        }
      );


    const candidates: ActionCandidate[] =
      [];


    if (outstandingCents > 0) {
      candidates.push({
        id: "collections",
        label: "REVENUE WAITING",
        headline:
          `${moneyFromCents(
            outstandingCents
          )} is ready to collect`,
        detail:
          `${unpaidOrders} unpaid order${
            unpaidOrders === 1
              ? ""
              : "s"
          } ${
            unpaidOrders === 1
              ? "is"
              : "are"
          } holding cash outside the business.`,
        metric:
          moneyFromCents(
            outstandingCents
          ),
        button:
          "OPEN REVENUE ENGINE",
        selector:
          ".revenue-command-center",
        revenueCents:
          outstandingCents,
        urgency: 100,
        probability: 95,
        nextMove:
          "Open the Revenue Engine and collect the unpaid balances.",
      });
    }


    if (outOfStock.length > 0) {
      candidates.push({
        id: "out-of-stock",
        label: "INVENTORY STOP",
        headline:
          `${outOfStock.length} product${
            outOfStock.length === 1
              ? " is"
              : "s are"
          } blocking buyer flow`,
        detail:
          "Restore inventory before the next buyer reaches a dead-end product.",
        metric:
          outOfStockRiskCents > 0
            ? moneyFromCents(
                outOfStockRiskCents
              )
            : `${outOfStock.length} OUT`,
        button:
          "VIEW INVENTORY",
        selector:
          ".metric-grid",
        revenueCents:
          outOfStockRiskCents,
        urgency: 96,
        probability: 98,
        nextMove:
          "Restock the unavailable products and restore the buyer path.",
      });
    }


    for (
      const lead of activeLeads.slice(0, 8)
    ) {
      const business =
        textValue(
          lead,
          [
            "business_name",
            "business",
            "company",
            "store_name",
            "name",
          ]
        ) ||
        "Buyer opportunity";

      const leadIndex =
        Math.max(
          0,
          leadRows.indexOf(lead)
        );

      const pipelineKey =
        ownerActionPipelineKey(
          lead,
          leadIndex
        );

      const deal =
        pipeline[pipelineKey];

      const stage =
        deal?.stage ||
        textValue(
          lead,
          [
            "stage",
            "status",
            "pipeline_stage",
          ]
        ) ||
        "Open";

      if (
        [
          "won",
          "lost",
          "closed",
          "cancelled",
          "canceled",
        ].includes(
          stage.toLowerCase()
        )
      ) {
        continue;
      }

      const postgresDealValue =
        Number(
          deal?.dealValue ||
          0
        );

      const valueCents =
        Number.isFinite(
          postgresDealValue
        ) &&
        postgresDealValue > 0
          ? Math.round(
              postgresDealValue * 100
            )
          : leadValueCents(lead);

      const probability =
        leadProbability(lead);

      const urgency =
        leadUrgency(lead);

      const id =
        textValue(
          lead,
          [
            "id",
            "lead_id",
            "email",
          ]
        ) ||
        business;

      const closeLanguage =
        probability >= 70
          ? "CLOSE"
          : "FOLLOW UP";

      candidates.push({
        id:
          `buyer-${id}`,
        label:
          probability >= 70
            ? "CLOSE OPPORTUNITY"
            : "BUYER ACTION",
        headline:
          `${closeLanguage} ${business}`,
        detail:
          `${stage} stage ? ${
            valueCents > 0
              ? `${moneyFromCents(
                  valueCents
                )} opportunity`
              : "value not yet confirmed"
          }.`,
        metric:
          valueCents > 0
            ? moneyFromCents(
                valueCents
              )
            : `${probability}% WIN`,
        button:
          "OPEN PRIORITY ENGINE",
        selector:
          ".priority-engine",
        revenueCents:
          valueCents,
        urgency,
        probability,
        nextMove:
          deal?.nextAction?.trim() ||
          leadNextMove(lead),
      });
    }


    if (lowStock.length > 0) {
      candidates.push({
        id: "low-stock",
        label: "STOCK WARNING",
        headline:
          `${lowStock.length} product${
            lowStock.length === 1
              ? " is"
              : "s are"
          } running low`,
        detail:
          "Inventory is still sellable, but revenue exposure is rising.",
        metric:
          lowStockRiskCents > 0
            ? moneyFromCents(
                lowStockRiskCents
              )
            : `${lowStock.length} LOW`,
        button:
          "VIEW INVENTORY",
        selector:
          ".metric-grid",
        revenueCents:
          lowStockRiskCents,
        urgency: 62,
        probability: 90,
        nextMove:
          "Replenish low-stock products before they interrupt buyer flow.",
      });
    }


    if (candidates.length === 0) {
      const clear: ActionSignal = {
        id: "clear",
        score: 0,
        level: "clear",
        label: "SYSTEM CLEAR",
        headline:
          "No urgent owner action detected",
        detail:
          "Revenue, buyer activity, and inventory are currently inside normal operating ranges.",
        metric: "CLEAR",
        button:
          "OPEN PRIORITY ENGINE",
        selector:
          ".priority-engine",
        revenueCents: 0,
        urgency: 0,
        probability: 100,
        nextMove:
          "Keep selling and monitor the next incoming buyer or order.",
      };

      return {
        signals: [clear],
        primary: clear,
        outstandingCents,
        unpaidOrders,
        outOfStockCount:
          outOfStock.length,
        lowStockCount:
          lowStock.length,
        activeLeadCount:
          activeLeads.length,
        opportunityCents: 0,
      };
    }


    const maxRevenueCents = Math.max(
      1,
      ...candidates.map(
        (candidate) =>
          candidate.revenueCents
      )
    );


    const signals: ActionSignal[] =
      candidates
        .map((candidate) => {
          const moneyImpact =
            candidate.revenueCents > 0
              ? (
                  candidate.revenueCents /
                  maxRevenueCents
                ) *
                45
              : 0;

          const urgencyImpact =
            candidate.urgency * 0.30;

          const probabilityImpact =
            candidate.probability * 0.25;

          const score = clamp(
            Math.round(
              moneyImpact +
              urgencyImpact +
              probabilityImpact
            ),
            0,
            100
          );

          return {
            ...candidate,
            score,
            level:
              levelForScore(score),
          };
        })
        .sort(
          (a, b) =>
            b.score - a.score
        );


    const opportunityCents =
      signals.reduce(
        (sum, signal) =>
          sum +
          Math.max(
            0,
            signal.revenueCents
          ),
        0
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
      opportunityCents,
    };
  }, [
    orders,
    products,
    setupRequests,
    pipeline,
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
        `${signal.label}: ${signal.nextMove}`
      );

      return;
    }

    setStatus(
      `${signal.label}: ${signal.nextMove}`
    );
  };


  const findLeadForSignal = (
    signal: ActionSignal
  ): Record<string, unknown> => {
    if (
      !signal.id.startsWith(
        "buyer-"
      )
    ) {
      return {};
    }

    const leadRows =
      setupRequests.map(asRecord);

    for (const lead of leadRows) {
      const business =
        textValue(
          lead,
          [
            "business_name",
            "business",
            "company",
            "store_name",
            "name",
          ]
        ) || "Buyer opportunity";

      const id =
        textValue(
          lead,
          [
            "id",
            "lead_id",
            "email",
          ]
        ) || business;

      if (
        `buyer-${id}` === signal.id
      ) {
        return lead;
      }
    }

    return {};
  };


  const findTopUnpaidOrder = () => {
    const candidates =
      orders
        .map(asRecord)
        .map((order) => {
          const paymentStatus =
            textValue(
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
            paymentStatus === "cancelled" ||
            paymentStatus === "canceled"
          ) {
            return {
              order,
              openBalance: 0,
            };
          }

          const totalCents =
            numberValue(
              order,
              [
                "total_cents",
                "totalCents",
              ]
            );

          const paidCents =
            numberValue(
              order,
              [
                "amount_paid_cents",
                "amountPaidCents",
              ]
            );

          return {
            order,
            openBalance:
              Math.max(
                0,
                totalCents - paidCents
              ),
          };
        })
        .filter(
          (candidate) =>
            candidate.openBalance > 0
        )
        .sort(
          (a, b) =>
            b.openBalance -
            a.openBalance
        );

    return candidates[0] || null;
  };


  const findStockProduct = (
    signal: ActionSignal
  ): Record<string, unknown> => {
    const rows =
      products.map(asRecord);

    const matches =
      rows.filter((product) => {
        const stock =
          numberValue(
            product,
            [
              "stock",
              "inventory",
            ]
          );

        if (
          signal.id ===
          "out-of-stock"
        ) {
          return stock <= 0;
        }

        if (
          signal.id ===
          "low-stock"
        ) {
          return (
            stock > 0 &&
            stock <= 3
          );
        }

        return false;
      });

    matches.sort(
      (a, b) =>
        numberValue(
          b,
          [
            "price_cents",
            "priceCents",
          ]
        ) -
        numberValue(
          a,
          [
            "price_cents",
            "priceCents",
          ]
        )
    );

    return matches[0] || {};
  };


  const buildExecutableAction = (
    signal: ActionSignal
  ) => {
    if (
      signal.id === "collections"
    ) {
      const candidate =
        findTopUnpaidOrder();

      if (!candidate) {
        return {
          message:
            signal.nextMove,
          email: "",
          subject:
            "Payment follow-up",
          status:
            "No unpaid order could be isolated.",
        };
      }

      const order =
        candidate.order;

      const orderId =
        textValue(
          order,
          [
            "id",
            "order_id",
            "orderId",
          ]
        ) || "current order";

      const buyer =
        textValue(
          order,
          [
            "customer_name",
            "customerName",
            "buyer_name",
            "buyerName",
            "name",
          ]
        ) || "there";

      const email =
        textValue(
          order,
          [
            "customer_email",
            "customerEmail",
            "buyer_email",
            "buyerEmail",
            "email",
          ]
        );

      const openBalance =
        candidate.openBalance;

      const message = [
        `Hi ${buyer},`,
        "",
        `I'm following up on the remaining ${moneyFromCents(
          openBalance
        )} balance for order ${orderId}.`,
        "",
        "Please let me know once payment is complete or if you need anything from me to finish it.",
        "",
        "Thank you,",
        "Andrew Wolverton",
      ].join("\n");

      return {
        message,
        email,
        subject:
          `Payment follow-up - ${orderId}`,
        status:
          `${moneyFromCents(
            openBalance
          )} collection action prepared for ${orderId}.`,

        // WOLF_OS_COLLECTION_TARGET_BRIDGE_V1
        // Expose target metadata only.
        // This does not mutate order/payment state.
        orderId:
          orderId === "current order"
            ? ""
            : orderId,
        buyer,
        openBalance,
      };
    }


    if (
      signal.id.startsWith(
        "buyer-"
      )
    ) {
      const lead =
        findLeadForSignal(signal);

      const buyer =
        textValue(
          lead,
          [
            "name",
            "contact_name",
            "contact",
          ]
        ) || "there";

      const business =
        textValue(
          lead,
          [
            "business_name",
            "business",
            "company",
            "store_name",
          ]
        ) || "your business";

      const email =
        textValue(
          lead,
          [
            "email",
            "contact_email",
            "owner_email",
          ]
        );

      const message = [
        `Hi ${buyer},`,
        "",
        `I wanted to follow up on ${business}.`,
        "",
        signal.nextMove,
        "",
        "If you're ready to move forward, reply and I'll lock in the next step.",
        "",
        "Andrew Wolverton",
        "I AM THE ONE™ / WOLF OS™",
      ].join("\n");

      return {
        message,
        email,
        subject:
          `Next step for ${business}`,
        status:
          email
            ? `Follow-up prepared for ${business}.`
            : `Follow-up copied for ${business}; no buyer email is currently loaded.`,
      };
    }


    if (
      signal.id === "out-of-stock" ||
      signal.id === "low-stock"
    ) {
      const product =
        findStockProduct(signal);

      const productName =
        textValue(
          product,
          [
            "name",
            "product_name",
            "sku",
          ]
        ) || "inventory item";

      const stock =
        numberValue(
          product,
          [
            "stock",
            "inventory",
          ]
        );

      const message = [
        "WOLF OS™ INVENTORY ACTION",
        "",
        `Product: ${productName}`,
        `Current stock: ${stock}`,
        `Revenue exposure: ${moneyFromCents(
          signal.revenueCents
        )}`,
        "",
        signal.nextMove,
      ].join("\n");

      return {
        message,
        email: "",
        subject:
          `Inventory action - ${productName}`,
        status:
          `Inventory action prepared for ${productName}.`,
      };
    }


    return {
      message:
        signal.nextMove,
      email: "",
      subject:
        "WOLF OS next action",
      status:
        signal.nextMove,
    };
  };


  const executeAction = async (
    signal: ActionSignal
  ) => {
    const action =
      buildExecutableAction(
        signal
      );

    executeFocus(signal);

    // WOLF_OS_COLLECTION_TARGET_BRIDGE_V1
    // Route collection work to the exact unpaid order.
    // No automatic payment update and no automatic email.
    if (signal.id === "collections") {
      const targetOrderId = String(
        (
          action as {
            orderId?: string;
          }
        ).orderId || ""
      ).trim();

      if (targetOrderId) {
        window.setTimeout(() => {
          window.dispatchEvent(
            new CustomEvent(
              "wolf-os-collection-target-v1",
              {
                detail: {
                  orderId: targetOrderId
                }
              }
            )
          );
        }, 0);
      }
    }

    let copied = false;

    try {
      await navigator.clipboard.writeText(
        action.message
      );

      copied = true;
    } catch {
      copied = false;
    }

    setStatus(
      copied
        ? `${action.status} Action copied.`
        : action.status
    );

    if (action.email) {
      setStatus(
        copied
          ? `${action.status} Email copied for ${action.email}.`
          : `${action.status} Buyer email: ${action.email}.`
      );
    }
  };


  const copyAction = async () => {
    const signal =
      intelligence.primary;

    const expectedValue =
      Math.round(
        signal.revenueCents *
        (
          signal.probability /
          100
        )
      );

    const plan = [
      "WOLF OS™ NEXT BEST ACTION",
      "",
      signal.label,
      signal.headline,
      signal.detail,
      "",
      `NEXT MOVE: ${signal.nextMove}`,
      "",
      `Priority score: ${signal.score}/100`,
      `Revenue impact: ${moneyFromCents(
        signal.revenueCents
      )}`,
      `Expected value: ${moneyFromCents(
        expectedValue
      )}`,
      `Urgency: ${signal.urgency}/100`,
      `Probability: ${signal.probability}%`,
      "",
      `Open cash: ${moneyFromCents(
        intelligence.outstandingCents
      )}`,
      `Active buyers: ${intelligence.activeLeadCount}`,
      `Out of stock: ${intelligence.outOfStockCount}`,
      `Low stock: ${intelligence.lowStockCount}`,
    ].join("\n");

    try {
      await navigator.clipboard.writeText(
        plan
      );

      setStatus(
        "Revenue-ranked action copied."
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
            WOLF OS™ OWNER ACTION ENGINE
          </p>

          <h2>
            Next Best Action
          </h2>

          <p className="owner-action-subtitle">
            Revenue impact, urgency, and probability ranked into one executable owner directive.
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

          <p>
            <strong>NEXT MOVE:</strong>{" "}
            {primary.nextMove}
          </p>

          <div className="owner-action-buttons">
            <button
              type="button"
              className="owner-action-button primary"
              onClick={() => {
                void executeAction(primary);
              }}
            >
              {primary.id === "clear"
                ? primary.button
                : "EXECUTE NEXT MOVE"}
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
            <span>
              REVENUE IMPACT
            </span>

            <strong>
              {moneyFromCents(
                primary.revenueCents
              )}
            </strong>
          </div>

          <div className="owner-action-stat">
            <span>
              URGENCY
            </span>

            <strong>
              {primary.urgency}/100
            </strong>
          </div>

          <div className="owner-action-stat">
            <span>
              WIN PROBABILITY
            </span>

            <strong>
              {primary.probability}%
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
                  #{signal.score} · {signal.label}
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
