import { useEffect, useMemo, useRef, useState } from "react";
import "./PriorityEngine.css";

type Stage =
  | "New"
  | "Contacted"
  | "Demo"
  | "Proposal"
  | "Closing"
  | "Won"
  | "Lost";

type PipelineState = {
  stage: Stage;
  dealValue: number;
  nextAction: string;
};

type Lead = {
  key: string;
  business: string;
  name: string;
  email: string;
  details: string;
  budget: string;
  timeline: string;
};

type Props = {
  setupRequests: unknown[];
};

type RankedTarget = {
  lead: Lead;
  deal: PipelineState;
  score: number;
  priority: string;
  reason: string;
  nextMove: string;
};

type FeedbackState =
  | "idle"
  | "locking"
  | "executed"
  | "closing"
  | "error";

const STORAGE_KEY =
  "wolf-os-buyer-pipeline-v2";

const PIPELINE_EVENT =
  "wolf-os-pipeline-updated";

const ACTIVITY_EVENT =
  "wolf-os-pipeline-activity-updated";

const API_BASE = String(
  import.meta.env.VITE_BACKEND_URL ||
    "http://127.0.0.1:5000"
).replace(/\/+$/, "");

const stages: Stage[] = [
  "New",
  "Contacted",
  "Demo",
  "Proposal",
  "Closing",
  "Won",
  "Lost",
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

  if (/5000/i.test(normalized)) {
    return 5000;
  }

  if (/3000/i.test(normalized)) {
    return 3000;
  }

  if (/2500/i.test(normalized)) {
    return 2500;
  }

  if (/1500/i.test(normalized)) {
    return 1500;
  }

  if (/750/i.test(normalized)) {
    return 750;
  }

  if (/499/i.test(normalized)) {
    return 499;
  }

  if (/299/i.test(normalized)) {
    return 299;
  }

  return 1500;
}

function defaultDeal(
  budget: string
): PipelineState {
  return {
    stage: "New",
    dealValue:
      defaultDealValue(budget),
    nextAction:
      "Contact buyer and schedule live demo",
  };
}

function loadPipeline(): Record<
  string,
  PipelineState
> {
  try {
    const raw =
      window.localStorage.getItem(
        STORAGE_KEY
      );

    if (!raw) {
      return {};
    }

    return JSON.parse(raw) as Record<
      string,
      PipelineState
    >;
  } catch {
    return {};
  }
}

function stageScore(stage: Stage) {
  switch (stage) {
    case "Closing":
      return 70;

    case "Proposal":
      return 55;

    case "Demo":
      return 40;

    case "Contacted":
      return 25;

    case "New":
      return 15;

    case "Won":
    case "Lost":
      return -1000;

    default:
      return 0;
  }
}

function timelineScore(
  timeline: string
) {
  const value =
    timeline.toLowerCase();

  if (
    value.includes("today") ||
    value.includes("immediate")
  ) {
    return 55;
  }

  if (
    value.includes("this week")
  ) {
    return 45;
  }

  if (
    value.includes("7 days")
  ) {
    return 35;
  }

  if (
    value.includes("soon")
  ) {
    return 25;
  }

  return 10;
}

function priorityLabel(
  score: number
) {
  if (score >= 120) {
    return "CRITICAL";
  }

  if (score >= 90) {
    return "HIGH";
  }

  if (score >= 60) {
    return "ACTIVE";
  }

  return "WATCH";
}

function nextMoveFor(
  stage: Stage
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

    default:
      return "Review the opportunity.";
  }
}

function reasonFor(
  lead: Lead,
  deal: PipelineState
) {
  const reasons: string[] = [];

  if (
    deal.dealValue >= 1500
  ) {
    reasons.push(
      "high-value opportunity"
    );
  }

  const timeline =
    lead.timeline.toLowerCase();

  if (
    timeline.includes("this week")
  ) {
    reasons.push(
      "this-week timeline"
    );
  } else if (
    timeline.includes("7 days")
  ) {
    reasons.push(
      "near-term follow-up window"
    );
  } else if (
    timeline.includes("soon")
  ) {
    reasons.push(
      "buyer indicated near-term interest"
    );
  }

  if (
    deal.stage === "Closing"
  ) {
    reasons.push(
      "deposit decision is near"
    );
  } else if (
    deal.stage === "Proposal"
  ) {
    reasons.push(
      "proposal is already in motion"
    );
  } else if (
    deal.stage === "Demo"
  ) {
    reasons.push(
      "buyer is inside the sales process"
    );
  } else if (
    deal.stage === "New"
  ) {
    reasons.push(
      "lead has not been worked yet"
    );
  }

  return reasons.length > 0
    ? reasons.join(" + ")
    : "active buyer opportunity";
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

export default function PriorityEngine({
  setupRequests,
}: Props) {
  const [pipeline, setPipeline] =
    useState<
      Record<string, PipelineState>
    >(loadPipeline);

  const [status, setStatus] =
    useState(
      "Priority Engine scanning live buyer opportunities..."
    );

  const [executing, setExecuting] =
    useState(false);

  const [feedbackState, setFeedbackState] =
    useState<FeedbackState>("idle");

  const [feedbackMessage, setFeedbackMessage] =
    useState("SYSTEM READY");

  const feedbackTimer =
    useRef<number | null>(null);

  const showFeedback = (
    state: FeedbackState,
    message: string,
    duration = 2200
  ) => {
    if (feedbackTimer.current !== null) {
      window.clearTimeout(
        feedbackTimer.current
      );
    }

    setFeedbackState(state);
    setFeedbackMessage(message);

    if (state !== "locking") {
      feedbackTimer.current =
        window.setTimeout(() => {
          setFeedbackState("idle");
          setFeedbackMessage(
            "SYSTEM READY"
          );

          feedbackTimer.current = null;
        }, duration);
    }
  };

  useEffect(() => {
    return () => {
      if (
        feedbackTimer.current !== null
      ) {
        window.clearTimeout(
          feedbackTimer.current
        );
      }
    };
  }, []);

  const leads = useMemo<Lead[]>(() => {
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
          details,
          budget,
          timeline,
        };
      }
    );
  }, [setupRequests]);

  useEffect(() => {
    const synchronize = () => {
      setPipeline(
        loadPipeline()
      );
    };

    synchronize();

    window.addEventListener(
      PIPELINE_EVENT,
      synchronize
    );

    window.addEventListener(
      "storage",
      synchronize
    );

    return () => {
      window.removeEventListener(
        PIPELINE_EVENT,
        synchronize
      );

      window.removeEventListener(
        "storage",
        synchronize
      );
    };
  }, []);

  const rankedTargets =
    useMemo<RankedTarget[]>(() => {
      return leads
        .map((lead) => {
          const deal =
            pipeline[lead.key] ||
            defaultDeal(
              lead.budget
            );

          const valueScore =
            Math.min(
              60,
              Math.round(
                deal.dealValue / 50
              )
            );

          const score =
            stageScore(
              deal.stage
            ) +
            timelineScore(
              lead.timeline
            ) +
            valueScore;

          return {
            lead,
            deal,
            score,
            priority:
              priorityLabel(score),
            reason: reasonFor(
              lead,
              deal
            ),
            nextMove: nextMoveFor(
              deal.stage
            ),
          };
        })
        .filter(
          ({ deal }) =>
            deal.stage !== "Won" &&
            deal.stage !== "Lost"
        )
        .sort(
          (a, b) =>
            b.score - a.score
        );
    }, [leads, pipeline]);

  const primaryTarget =
    rankedTargets[0];

  const activeMoney =
    rankedTargets.reduce(
      (total, target) =>
        total +
        target.deal.dealValue,
      0
    );

  const buildCloseMessage = (
    target: RankedTarget
  ) =>
    [
      `Hi ${target.lead.name},`,
      "",
      `I wanted to follow up about the ${target.lead.business} storefront and owner system.`,
      "",
      `Based on what you shared — ${target.lead.details} — I believe the next move is straightforward.`,
      "",
      `Recommended direction: ${target.lead.budget}`,
      `Current project value: ${money(target.deal.dealValue)}`,
      `Timeline: ${target.lead.timeline}`,
      "",
      target.nextMove,
      "",
      "I can walk you through the live system and confirm the exact build scope, deposit, and launch date.",
      "",
      "Are you ready to move forward?",
      "",
      "Andrew Wolverton",
      "I AM THE ONE™ · WOLF OS™",
    ].join("\n");

  const copyTargetMessage =
    async (
      target: RankedTarget
    ) => {
      const message =
        buildCloseMessage(target);

      try {
        if (
          navigator.clipboard
            ?.writeText
        ) {
          await navigator.clipboard.writeText(
            message
          );
        } else {
          copyFallback(message);
        }
      } catch {
        copyFallback(message);
      }

      setStatus(
        `${target.lead.business} priority close message copied.`
      );
    };

  const openTargetEmail = (
    target: RankedTarget
  ) => {
    if (!target.lead.email) {
      setStatus(
        `${target.lead.business} does not have an email address.`
      );

      return;
    }

    const subject =
      `${target.lead.business} storefront + owner system`;

    const body =
      buildCloseMessage(target);

    window.location.href =
      `mailto:${encodeURIComponent(
        target.lead.email
      )}?subject=${encodeURIComponent(
        subject
      )}&body=${encodeURIComponent(
        body
      )}`;

    setStatus(
      `${target.lead.business} priority email opened.`
    );
  };

  const executeNextMove =
    async (
      target: RankedTarget
    ) => {
      if (executing) {
        return;
      }

      if (
        target.deal.stage ===
        "Closing"
      ) {
        showFeedback(
          "closing",
          "CLOSING MODE · CLOSE MESSAGE ARMED",
          2800
        );

        await copyTargetMessage(
          target
        );

        setStatus(
          `${target.lead.business} is at CLOSING. Close message copied. Ask for the deposit before marking the deal Won.`
        );

        return;
      }

      const currentIndex =
        stages.indexOf(
          target.deal.stage
        );

      const nextStage =
        stages[
          Math.min(
            currentIndex + 1,
            stages.indexOf(
              "Closing"
            )
          )
        ];

      const nextDeal: PipelineState =
        {
          ...target.deal,
          stage: nextStage,
          nextAction:
            nextMoveFor(
              nextStage
            ),
        };

      const ownerToken =
        window.localStorage.getItem(
          "wolf_owner_token"
        ) || "";

      if (!ownerToken) {
        setStatus(
          "Unlock Owner Console before executing the priority move."
        );

        return;
      }

      setExecuting(true);

      showFeedback(
        "locking",
        `TARGET LOCK · ${target.lead.business.toUpperCase()}`
      );

      setStatus(
        `Executing next move for ${target.lead.business}...`
      );

      try {
        const response =
          await fetch(
            `${API_BASE}/api/owner/pipeline/${encodeURIComponent(
              target.lead.key
            )}`,
            {
              method: "PUT",
              headers: {
                Authorization:
                  `Bearer ${ownerToken}`,
                "Content-Type":
                  "application/json",
              },
              body: JSON.stringify({
                stage:
                  nextDeal.stage,
                deal_value:
                  nextDeal.dealValue,
                next_action:
                  nextDeal.nextAction,
              }),
            }
          );

        const payload =
          await response.json();

        if (
          !response.ok ||
          !payload?.ok
        ) {
          throw new Error(
            payload?.error ||
              `Priority action failed: ${response.status}`
          );
        }

        const nextPipeline = {
          ...loadPipeline(),
          [target.lead.key]:
            nextDeal,
        };

        window.localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify(
            nextPipeline
          )
        );

        setPipeline(
          nextPipeline
        );

        window.dispatchEvent(
          new CustomEvent(
            PIPELINE_EVENT
          )
        );

        window.dispatchEvent(
          new CustomEvent(
            ACTIVITY_EVENT
          )
        );

        showFeedback(
          "executed",
          `MOVE EXECUTED · ${target.deal.stage.toUpperCase()} → ${nextStage.toUpperCase()}`,
          2800
        );

        setStatus(
          `${target.lead.business} advanced from ${target.deal.stage} to ${nextStage}. Priority Engine recalculated the attack queue.`
        );
      } catch (error) {
        showFeedback(
          "error",
          "EXECUTION FAILED · CHECK SYSTEM",
          3200
        );

        setStatus(
          error instanceof Error
            ? `Priority Engine error: ${error.message}`
            : "Priority action failed."
        );
      } finally {
        setExecuting(false);
      }
    };

  if (!primaryTarget) {
    return (
      <section className="priority-engine priority-engine-clear">
        <div>
          <p className="priority-engine-kicker">
            WOLF OS™ PRIORITY ENGINE
          </p>

          <h2>
            Revenue Attack Queue Clear
          </h2>

          <p>
            No open buyer deals require
            action. Review won deals or
            capture a new setup request.
          </p>
        </div>

        <div className="priority-clear-badge">
          QUEUE CLEAR
        </div>
      </section>
    );
  }

  return (
    <section className="priority-engine">
      <div className="priority-engine-glow" />

      <header className="priority-engine-header">
        <div>
          <p className="priority-engine-kicker">
            WOLF OS™ PRIORITY ENGINE
          </p>

          <h2>
            Revenue Attack Queue
          </h2>

          <p>
            Rule-based operational
            prioritization using live deal
            stage, value, and buyer timeline.
          </p>
        </div>

        <div className="priority-engine-scan">
          <span />
          LIVE TARGETING
        </div>
      </header>

      <div className="priority-target-layout">
        <article
          className={`priority-primary-target feedback-${feedbackState}`}
        >
          <div
            className={`priority-execution-feedback ${feedbackState}`}
          >
            <span className="priority-feedback-light" />

            <strong>
              {feedbackMessage}
            </strong>
          </div>

          <div className="priority-execution-sweep" />

          <div className="priority-target-number">
            TARGET 01
          </div>

          <div className="priority-target-topline">
            <span
              className={`priority-level priority-${primaryTarget.priority.toLowerCase()}`}
            >
              {
                primaryTarget.priority
              }
            </span>

            <span className="priority-score">
              PRIORITY SCORE{" "}
              {
                primaryTarget.score
              }
            </span>
          </div>

          <h3>
            {
              primaryTarget.lead
                .business
            }
          </h3>

          <p className="priority-contact">
            {
              primaryTarget.lead
                .name
            }
            {primaryTarget.lead.email
              ? ` · ${primaryTarget.lead.email}`
              : ""}
          </p>

          <div className="priority-money">
            <span>
              MONEY AT STAKE
            </span>

            <strong>
              {money(
                primaryTarget.deal
                  .dealValue
              )}
            </strong>
          </div>

          <div className="priority-reason">
            <span>
              WHY THIS TARGET
            </span>

            <p>
              {
                primaryTarget.reason
              }
            </p>
          </div>

          <div className="priority-next-move">
            <span>
              EXECUTE NEXT MOVE
            </span>

            <strong>
              {
                primaryTarget.nextMove
              }
            </strong>
          </div>

          <div className="priority-actions">
            <button
              type="button"
              className="priority-execute-button"
              disabled={executing}
              onClick={() =>
                void executeNextMove(
                  primaryTarget
                )
              }
            >
              {executing
                ? feedbackState === "locking"
                  ? "TARGET LOCK..."
                  : "EXECUTING..."
                : "EXECUTE NEXT MOVE"}
            </button>

            <button
              type="button"
              onClick={() =>
                void copyTargetMessage(
                  primaryTarget
                )
              }
            >
              COPY CLOSE MESSAGE
            </button>

            <button
              type="button"
              onClick={() =>
                openTargetEmail(
                  primaryTarget
                )
              }
            >
              OPEN BUYER EMAIL
            </button>
          </div>
        </article>

        <aside className="priority-queue-panel">
          <div className="priority-queue-summary">
            <span>
              ACTIVE TARGETS
            </span>

            <strong>
              {rankedTargets.length}
            </strong>
          </div>

          <div className="priority-queue-summary">
            <span>
              MONEY IN QUEUE
            </span>

            <strong>
              {money(activeMoney)}
            </strong>
          </div>

          <div className="priority-queue-list">
            {rankedTargets
              .slice(0, 3)
              .map(
                (
                  target,
                  index
                ) => (
                  <article
                    key={
                      target.lead.key
                    }
                    className={
                      index === 0
                        ? "priority-queue-card active"
                        : "priority-queue-card"
                    }
                  >
                    <span>
                      0{index + 1}
                    </span>

                    <div>
                      <strong>
                        {
                          target.lead
                            .business
                        }
                      </strong>

                      <small>
                        {
                          target.deal
                            .stage
                        }
                        {" · "}
                        {money(
                          target.deal
                            .dealValue
                        )}
                      </small>
                    </div>

                    <b>
                      {
                        target.priority
                      }
                    </b>
                  </article>
                )
              )}
          </div>
        </aside>
      </div>

      <footer className="priority-engine-status">
        <span>
          SYSTEM COMMAND
        </span>

        <p>
          {status}
        </p>
      </footer>
    </section>
  );
}
