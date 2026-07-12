import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  type PipelineStage,
  type PipelineState,
  saveUnifiedPipelineDeal,
  useUnifiedPipeline,
} from "../lib/pipelineState";

import "./BuyerPipelineBoard.css";

type Lead = {
  key: string;
  business: string;
  name: string;
  email: string;
  phone: string;
  details: string;
  budget: string;
  timeline: string;
};

type Props = {
  setupRequests: unknown[];
  ownerToken?: string;
};

const stages: PipelineStage[] = [
  "New",
  "Contacted",
  "Demo",
  "Proposal",
  "Closing",
  "Won",
  "Lost",
];

const stageRank:
  Record<PipelineStage, number> = {
    New: 1,
    Contacted: 2,
    Demo: 3,
    Proposal: 4,
    Closing: 5,
    Won: 6,
    Lost: 0,
  };

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

function asRecord(
  value: unknown
): Record<string, unknown> {
  if (
    typeof value === "object" &&
    value !== null
  ) {
    return value as Record<
      string,
      unknown
    >;
  }

  return {};
}

function valueText(
  record: Record<string, unknown>,
  keys: string[],
  fallback = ""
) {
  for (const key of keys) {
    const value = record[key];

    if (
      typeof value === "string" &&
      value.trim()
    ) {
      return value.trim();
    }

    if (
      typeof value === "number"
    ) {
      return String(value);
    }
  }

  return fallback;
}

function defaultDealValue(
  budget: string
) {
  const normalized =
    budget.replace(/,/g, "");

  if (/5000/i.test(normalized)) return 5000;
  if (/3000/i.test(normalized)) return 3000;
  if (/2500/i.test(normalized)) return 2500;
  if (/1500/i.test(normalized)) return 1500;
  if (/750/i.test(normalized)) return 750;
  if (/499/i.test(normalized)) return 499;
  if (/299/i.test(normalized)) return 299;

  return 1500;
}

function nextActionForStage(
  stage: PipelineStage
) {
  switch (stage) {
    case "New":
      return "Contact buyer and open the conversation.";

    case "Contacted":
      return "Schedule and run the live WOLF OS demo.";

    case "Demo":
      return "Send the recommended package and proposal.";

    case "Proposal":
      return "Follow up directly and move the buyer toward the deposit.";

    case "Closing":
      return "Ask for the deposit and confirm the launch date.";

    case "Won":
      return "Begin onboarding and production setup.";

    case "Lost":
      return "Review the loss reason and decide whether to re-engage.";
  }
}

function defaultDeal(
  budget = ""
): PipelineState {
  return {
    stage: "New",
    dealValue:
      defaultDealValue(budget),
    nextAction:
      nextActionForStage("New"),
  };
}

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

export default function BuyerPipelineBoard({
  setupRequests,
  ownerToken = "",
}: Props) {
  const {
    pipeline,
    pipelineReady,
    pipelineStatus,
    refreshPipeline,
  } = useUnifiedPipeline(
    ownerToken
  );

  const [status, setStatus] =
    useState("");

  const [copiedKey, setCopiedKey] =
    useState("");

  const provisioning =
    useRef(false);

  const leads = useMemo<Lead[]>(
    () => {
      return setupRequests.map(
        (rawLead, index) => {
          const lead =
            asRecord(rawLead);

          const business = valueText(
            lead,
            [
              "business_name",
              "businessName",
              "business",
            ],
            `Buyer Lead ${index + 1}`
          );

          const name = valueText(
            lead,
            [
              "name",
              "contact_name",
              "contactName",
            ],
            "Buyer"
          );

          const email = valueText(
            lead,
            ["email"]
          );

          const phone = valueText(
            lead,
            [
              "phone",
              "phone_number",
            ]
          );

          const details = valueText(
            lead,
            [
              "what_i_sell",
              "whatISell",
              "business_details",
              "details",
            ],
            "Business setup opportunity"
          );

          const budget = valueText(
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
              .filter(([key]) =>
                /budget|package/i.test(
                  key
                )
              )
              .map(([, value]) =>
                typeof value ===
                  "string" ||
                typeof value ===
                  "number"
                  ? String(
                      value
                    ).trim()
                  : ""
              )
              .find(Boolean) ||
              "Package not selected"
          );

          const timeline = valueText(
            lead,
            ["timeline"],
            "Timeline not selected"
          );

          const id = valueText(
            lead,
            [
              "id",
              "request_id",
              "created_at",
            ]
          );

          return {
            key:
              id ||
              `${business}-${email || name}-${index}`,
            business,
            name,
            email,
            phone,
            details,
            budget,
            timeline,
          };
        }
      );
    },
    [setupRequests]
  );

  useEffect(() => {
    if (
      !pipelineReady ||
      provisioning.current
    ) {
      return;
    }

    const missing =
      leads.filter(
        (lead) =>
          !pipeline[lead.key]
      );

    if (
      missing.length === 0
    ) {
      return;
    }

    provisioning.current = true;

    const provision = async () => {
      try {
        for (
          const lead of missing
        ) {
          await saveUnifiedPipelineDeal(
            lead.key,
            defaultDeal(
              lead.budget
            ),
            ownerToken
          );
        }

        await refreshPipeline();

        setStatus(
          `${missing.length} new buyer deal${missing.length === 1 ? "" : "s"} added to SQLite.`
        );

      } catch (error) {
        setStatus(
          error instanceof Error
            ? `Deal provision error: ${error.message}`
            : "New buyer deals could not be created."
        );

      } finally {
        provisioning.current = false;
      }
    };

    void provision();
  }, [
    leads,
    ownerToken,
    pipeline,
    pipelineReady,
    refreshPipeline,
  ]);

  const pipelineRows =
    useMemo(() => {
      return leads
        .map((lead) => ({
          lead,
          deal:
            pipeline[lead.key] ||
            defaultDeal(
              lead.budget
            ),
        }))
        .sort(
          (a, b) =>
            stageRank[
              b.deal.stage
            ] -
              stageRank[
                a.deal.stage
              ] ||
            b.deal.dealValue -
              a.deal.dealValue
        );
    }, [leads, pipeline]);

  const activePipeline =
    pipelineRows
      .filter(
        ({ deal }) =>
          deal.stage !== "Won" &&
          deal.stage !== "Lost"
      )
      .reduce(
        (total, { deal }) =>
          total +
          deal.dealValue,
        0
      );

  const wonRevenue =
    pipelineRows
      .filter(
        ({ deal }) =>
          deal.stage === "Won"
      )
      .reduce(
        (total, { deal }) =>
          total +
          deal.dealValue,
        0
      );

  const hotDeals =
    pipelineRows.filter(
      ({ deal }) =>
        [
          "Demo",
          "Proposal",
          "Closing",
        ].includes(
          deal.stage
        )
    ).length;

  const closingRevenue =
    pipelineRows
      .filter(
        ({ deal }) =>
          deal.stage ===
          "Closing"
      )
      .reduce(
        (total, { deal }) =>
          total +
          deal.dealValue,
        0
      );

  const persistDeal =
    async (
      leadId: string,
      deal: PipelineState
    ) => {
      setStatus(
        "Saving deal to SQLite..."
      );

      try {
        await saveUnifiedPipelineDeal(
          leadId,
          deal,
          ownerToken
        );

        setStatus(
          "Deal saved. All WOLF OS pipeline systems synchronized."
        );

      } catch (error) {
        setStatus(
          error instanceof Error
            ? `Deal save error: ${error.message}`
            : "Deal could not be saved."
        );
      }
    };

  const advanceDeal = (
    key: string,
    deal: PipelineState
  ) => {
    if (
      deal.stage === "Won" ||
      deal.stage === "Lost"
    ) {
      setStatus(
        "Closed deals stay locked until the stage is manually changed."
      );

      return;
    }

    const currentIndex =
      stages.indexOf(
        deal.stage
      );

    const nextStage =
      stages[
        Math.min(
          currentIndex + 1,
          stages.indexOf("Won")
        )
      ];

    void persistDeal(
      key,
      {
        ...deal,
        stage: nextStage,
        nextAction:
          nextActionForStage(
            nextStage
          ),
      }
    );
  };

  const buildFollowUp = (
    lead: Lead,
    deal: PipelineState
  ) =>
    [
      `Hi ${lead.name},`,
      "",
      `Following up about the ${lead.business} storefront and owner system.`,
      "",
      `Based on what you shared — ${lead.details} — I have the opportunity at the ${deal.stage} stage.`,
      "",
      `Current project direction: ${lead.budget}`,
      `Target project value: ${money(deal.dealValue)}`,
      `Timeline: ${lead.timeline}`,
      "",
      deal.nextAction,
      "",
      "I can walk you through the live storefront, checkout flow, owner dashboard, orders, inventory, leads, and business intelligence system.",
      "",
      "The next step is confirming the build scope, deposit, and launch timeline.",
      "",
      "Are you ready to move forward?",
      "",
      "Andrew Wolverton",
      "I AM THE ONE™ · WOLF OS™",
    ].join("\n");

  const copyFollowUp =
    async (
      lead: Lead,
      deal: PipelineState
    ) => {
      const text =
        buildFollowUp(
          lead,
          deal
        );

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
      } catch {
        copyFallback(text);
      }

      setCopiedKey(
        lead.key
      );

      setStatus(
        `${lead.business} buyer follow-up copied.`
      );

      window.setTimeout(
        () => setCopiedKey(""),
        1600
      );
    };

  const openEmail = (
    lead: Lead,
    deal: PipelineState
  ) => {
    if (!lead.email) {
      setStatus(
        `${lead.business} does not have an email address.`
      );

      return;
    }

    const subject =
      `${lead.business} storefront + owner system`;

    const body =
      buildFollowUp(
        lead,
        deal
      );

    window.location.href =
      `mailto:${encodeURIComponent(
        lead.email
      )}?subject=${encodeURIComponent(
        subject
      )}&body=${encodeURIComponent(
        body
      )}`;

    setStatus(
      `${lead.business} email draft opened.`
    );
  };

  return (
    <section className="buyer-pipeline-board">
      <header className="buyer-pipeline-header">
        <div>
          <p className="buyer-pipeline-kicker">
            WOLF OS™ DEAL DESK
          </p>

          <h2>
            Live Buyer Pipeline
          </h2>

          <p>
            SQLite is the single source
            of truth for every WOLF OS
            sales system.
          </p>
        </div>

        <div className="buyer-pipeline-live">
          <span />

          {leads.length} LIVE BUYER
          {leads.length === 1
            ? ""
            : "S"}

          {" · "}SQLITE AUTHORITY
        </div>
      </header>

      <div className="buyer-pipeline-metrics">
        <article>
          <span>
            Active Pipeline
          </span>

          <strong>
            {money(activePipeline)}
          </strong>

          <small>
            Open buyer opportunities
          </small>
        </article>

        <article>
          <span>
            Hot Deals
          </span>

          <strong>
            {hotDeals}
          </strong>

          <small>
            Demo through closing
          </small>
        </article>

        <article>
          <span>
            Closing Revenue
          </span>

          <strong>
            {money(
              closingRevenue
            )}
          </strong>

          <small>
            Deals at final stage
          </small>
        </article>

        <article className="buyer-pipeline-won">
          <span>
            Won Revenue
          </span>

          <strong>
            {money(wonRevenue)}
          </strong>

          <small>
            Closed business
          </small>
        </article>
      </div>

      <div className="buyer-pipeline-status">
        {status ||
          pipelineStatus}
      </div>

      <div className="buyer-deal-stack">
        {pipelineRows.length === 0 ? (
          <div className="buyer-pipeline-empty">
            No live setup requests yet.
          </div>
        ) : (
          pipelineRows.map(
            ({ lead, deal }) => (
              <article
                className="buyer-deal-card"
                key={lead.key}
              >
                <div className="buyer-deal-main">
                  <div className="buyer-deal-identity">
                    <span
                      className={`buyer-stage stage-${deal.stage.toLowerCase()}`}
                    >
                      {deal.stage}
                    </span>

                    <h3>
                      {lead.business}
                    </h3>

                    <p>
                      {lead.name}

                      {lead.email
                        ? ` · ${lead.email}`
                        : ""}
                    </p>
                  </div>

                  <div className="buyer-deal-value">
                    <span>
                      Deal Value
                    </span>

                    <strong>
                      {money(
                        deal.dealValue
                      )}
                    </strong>
                  </div>
                </div>

                <p className="buyer-deal-details">
                  {lead.details}
                </p>

                <div className="buyer-deal-meta">
                  <span>
                    <b>Budget</b>
                    {lead.budget}
                  </span>

                  <span>
                    <b>Timeline</b>
                    {lead.timeline}
                  </span>

                  {lead.phone ? (
                    <span>
                      <b>Phone</b>
                      {lead.phone}
                    </span>
                  ) : null}
                </div>

                <div className="buyer-deal-controls">
                  <label>
                    Sales stage

                    <select
                      value={
                        deal.stage
                      }
                      onChange={(event) => {
                        const stage =
                          event.target
                            .value as PipelineStage;

                        void persistDeal(
                          lead.key,
                          {
                            ...deal,
                            stage,
                            nextAction:
                              nextActionForStage(
                                stage
                              ),
                          }
                        );
                      }}
                    >
                      {stages.map(
                        (stage) => (
                          <option
                            key={stage}
                            value={stage}
                          >
                            {stage}
                          </option>
                        )
                      )}
                    </select>
                  </label>

                  <label>
                    Deal value

                    <input
                      key={`${lead.key}-${deal.dealValue}`}
                      type="number"
                      min="0"
                      step="100"
                      defaultValue={
                        deal.dealValue
                      }
                      onBlur={(event) => {
                        const value =
                          Math.max(
                            0,
                            Number(
                              event.target
                                .value
                            ) || 0
                          );

                        if (
                          value !==
                          deal.dealValue
                        ) {
                          void persistDeal(
                            lead.key,
                            {
                              ...deal,
                              dealValue:
                                value,
                            }
                          );
                        }
                      }}
                    />
                  </label>

                  <label className="buyer-next-action">
                    Next action

                    <input
                      key={`${lead.key}-${deal.nextAction}`}
                      defaultValue={
                        deal.nextAction
                      }
                      onBlur={(event) => {
                        const value =
                          event.target
                            .value.trim();

                        if (
                          value !==
                          deal.nextAction
                        ) {
                          void persistDeal(
                            lead.key,
                            {
                              ...deal,
                              nextAction:
                                value,
                            }
                          );
                        }
                      }}
                    />
                  </label>
                </div>

                <div className="buyer-deal-actions">
                  <button
                    type="button"
                    className="buyer-deal-primary"
                    onClick={() =>
                      advanceDeal(
                        lead.key,
                        deal
                      )
                    }
                  >
                    Advance Deal
                  </button>

                  <button
                    type="button"
                    className={
                      copiedKey ===
                      lead.key
                        ? "buyer-copied"
                        : ""
                    }
                    onClick={() =>
                      void copyFollowUp(
                        lead,
                        deal
                      )
                    }
                  >
                    {copiedKey ===
                    lead.key
                      ? "Follow-up Copied"
                      : "Copy Follow-up"}
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      openEmail(
                        lead,
                        deal
                      )
                    }
                  >
                    Open Buyer Email
                  </button>
                </div>
              </article>
            )
          )
        )}
      </div>
    </section>
  );
}
