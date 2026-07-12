from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"
COMPONENTS = SRC / "components"

APP = SRC / "App.tsx"

COMPONENT = COMPONENTS / "PriorityEngine.tsx"
CSS = COMPONENTS / "PriorityEngine.css"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Priority Engine patch starting...")


def backup(path: Path, label: str) -> Path:
    backup_dir = ROOT / "backups" / "priority-engine"

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = backup_dir / (
        f"{path.stem}-{label}-{stamp}{path.suffix}"
    )

    shutil.copy2(
        path,
        target,
    )

    print(f"Backup created: {target}")

    return target


def replace_once(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    if old not in text:
        raise SystemExit(
            f"PATCH STOPPED: Could not locate {label}."
        )

    print(f"Patched: {label}")

    return text.replace(
        old,
        new,
        1,
    )


if not APP.exists():
    raise SystemExit(
        f"App.tsx not found: {APP}"
    )


backup(
    APP,
    "before-priority-engine",
)


component_code = r'''import { useEffect, useMemo, useState } from "react";
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

        setStatus(
          `${target.lead.business} advanced from ${target.deal.stage} to ${nextStage}. Priority Engine recalculated the attack queue.`
        );
      } catch (error) {
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
        <article className="priority-primary-target">
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
                ? "EXECUTING..."
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
'''


css_code = r'''.priority-engine {
  position: relative;
  overflow: hidden;
  margin-top: 28px;
  padding: 26px;
  border: 1px solid rgba(255, 74, 50, 0.34);
  border-radius: 24px;
  background:
    radial-gradient(circle at 4% 4%, rgba(255, 48, 28, 0.15), transparent 31%),
    radial-gradient(circle at 92% 8%, rgba(255, 150, 25, 0.08), transparent 25%),
    linear-gradient(145deg, rgba(14, 7, 7, 0.99), rgba(4, 4, 7, 0.99));
  box-shadow:
    0 28px 80px rgba(0, 0, 0, 0.52),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.priority-engine * {
  box-sizing: border-box;
}

.priority-engine-glow {
  position: absolute;
  top: -150px;
  left: -110px;
  width: 380px;
  height: 380px;
  border-radius: 50%;
  background: rgba(255, 48, 25, 0.14);
  filter: blur(90px);
  pointer-events: none;
}

.priority-engine-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.priority-engine-kicker {
  margin: 0 0 7px;
  color: #ff624b;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.priority-engine-header h2,
.priority-engine-clear h2 {
  margin: 0;
  color: #fff;
  font-size: clamp(1.6rem, 3vw, 2.45rem);
  letter-spacing: -0.045em;
}

.priority-engine-header p,
.priority-engine-clear p {
  max-width: 740px;
  margin: 9px 0 0;
  color: rgba(239, 241, 247, 0.62);
  line-height: 1.55;
}

.priority-engine-scan {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  gap: 9px;
  padding: 10px 13px;
  border: 1px solid rgba(255, 80, 54, 0.38);
  border-radius: 999px;
  background: rgba(156, 35, 23, 0.18);
  color: #ff806c;
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.08em;
}

.priority-engine-scan span {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #ff4d36;
  box-shadow: 0 0 17px #ff4d36;
  animation: priority-pulse 1.4s ease-in-out infinite;
}

@keyframes priority-pulse {
  0%,
  100% {
    opacity: 0.45;
    transform: scale(0.86);
  }

  50% {
    opacity: 1;
    transform: scale(1.14);
  }
}

.priority-target-layout {
  position: relative;
  display: grid;
  grid-template-columns: 1.4fr 0.6fr;
  gap: 15px;
}

.priority-primary-target,
.priority-queue-panel {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 19px;
  background: rgba(255, 255, 255, 0.025);
}

.priority-primary-target {
  padding: 22px;
  border-color: rgba(255, 76, 50, 0.3);
  background:
    linear-gradient(140deg, rgba(255, 54, 33, 0.13), rgba(255, 255, 255, 0.018));
}

.priority-target-number {
  margin-bottom: 14px;
  color: rgba(255, 255, 255, 0.36);
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.16em;
}

.priority-target-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
}

.priority-level {
  display: inline-flex;
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 0.67rem;
  font-weight: 950;
  letter-spacing: 0.09em;
}

.priority-critical {
  border: 1px solid rgba(255, 78, 54, 0.55);
  background: rgba(200, 35, 24, 0.2);
  color: #ff7562;
  box-shadow: 0 0 22px rgba(255, 55, 34, 0.12);
}

.priority-high {
  border: 1px solid rgba(255, 172, 52, 0.5);
  background: rgba(181, 103, 17, 0.17);
  color: #ffc46d;
}

.priority-active {
  border: 1px solid rgba(85, 255, 166, 0.35);
  background: rgba(42, 149, 89, 0.12);
  color: #74ffb5;
}

.priority-watch {
  border: 1px solid rgba(127, 174, 255, 0.3);
  background: rgba(60, 105, 183, 0.1);
  color: #9cc1ff;
}

.priority-score {
  color: rgba(239, 243, 249, 0.43);
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.07em;
}

.priority-primary-target h3 {
  margin: 18px 0 0;
  color: #fff;
  font-size: clamp(1.65rem, 3.4vw, 3rem);
  letter-spacing: -0.05em;
}

.priority-contact {
  margin: 6px 0 0;
  color: rgba(237, 241, 247, 0.53);
  font-size: 0.82rem;
}

.priority-money {
  margin-top: 22px;
  padding: 18px;
  border: 1px solid rgba(255, 83, 52, 0.22);
  border-radius: 15px;
  background: rgba(0, 0, 0, 0.22);
}

.priority-money span,
.priority-reason span,
.priority-next-move span,
.priority-engine-status span,
.priority-queue-summary span {
  display: block;
  color: rgba(239, 243, 249, 0.47);
  font-size: 0.67rem;
  font-weight: 900;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.priority-money strong {
  display: block;
  margin-top: 7px;
  color: #ff6e55;
  font-size: clamp(2rem, 5vw, 4.4rem);
  letter-spacing: -0.06em;
}

.priority-reason,
.priority-next-move {
  margin-top: 14px;
  padding: 16px 18px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.026);
}

.priority-reason p {
  margin: 8px 0 0;
  color: rgba(238, 243, 248, 0.73);
  line-height: 1.5;
  text-transform: capitalize;
}

.priority-next-move {
  border-left: 3px solid #ff5139;
}

.priority-next-move strong {
  display: block;
  margin-top: 8px;
  color: #fff;
  font-size: clamp(1.05rem, 2vw, 1.4rem);
  line-height: 1.4;
}

.priority-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  margin-top: 17px;
}

.priority-actions button {
  padding: 12px 14px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-size: 0.73rem;
  font-weight: 950;
  cursor: pointer;
  transition:
    transform 150ms ease,
    border-color 150ms ease;
}

.priority-actions button:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 112, 83, 0.55);
}

.priority-actions button:disabled {
  opacity: 0.55;
  cursor: wait;
}

.priority-actions .priority-execute-button {
  border-color: #ff5038;
  background: linear-gradient(135deg, #ff3825, #ff7c45);
  color: #180300;
  box-shadow: 0 12px 35px rgba(255, 51, 30, 0.24);
}

.priority-queue-panel {
  padding: 18px;
}

.priority-queue-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.priority-queue-summary strong {
  color: #fff;
  font-size: 1.15rem;
}

.priority-queue-list {
  display: grid;
  gap: 9px;
  margin-top: 15px;
}

.priority-queue-card {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.022);
}

.priority-queue-card.active {
  border-color: rgba(255, 78, 50, 0.4);
  background: rgba(255, 56, 35, 0.08);
}

.priority-queue-card > span {
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.68rem;
  font-weight: 900;
}

.priority-queue-card strong,
.priority-queue-card small {
  display: block;
}

.priority-queue-card strong {
  color: #fff;
  font-size: 0.8rem;
}

.priority-queue-card small {
  margin-top: 4px;
  color: rgba(234, 240, 247, 0.47);
  font-size: 0.68rem;
}

.priority-queue-card b {
  color: #ff806c;
  font-size: 0.61rem;
}

.priority-engine-status {
  position: relative;
  margin-top: 15px;
  padding: 14px 16px;
  border-left: 3px solid #ff4d35;
  border-radius: 9px;
  background: rgba(255, 52, 31, 0.055);
}

.priority-engine-status p {
  margin: 6px 0 0;
  color: rgba(236, 242, 248, 0.69);
  line-height: 1.5;
}

.priority-engine-clear {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.priority-clear-badge {
  flex-shrink: 0;
  padding: 11px 15px;
  border: 1px solid rgba(78, 255, 166, 0.31);
  border-radius: 999px;
  background: rgba(35, 144, 86, 0.12);
  color: #70ffb1;
  font-size: 0.72rem;
  font-weight: 900;
}

@media (max-width: 1000px) {
  .priority-target-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 680px) {
  .priority-engine {
    padding: 18px;
  }

  .priority-engine-header,
  .priority-engine-clear,
  .priority-target-topline {
    align-items: flex-start;
    flex-direction: column;
  }

  .priority-actions,
  .priority-actions button {
    width: 100%;
  }

  .priority-queue-card {
    grid-template-columns: 25px 1fr;
  }

  .priority-queue-card b {
    grid-column: 2;
  }
}
'''


COMPONENT.write_text(
    component_code,
    encoding="utf-8",
)

CSS.write_text(
    css_code,
    encoding="utf-8",
)

print(
    f"Created: {COMPONENT}"
)

print(
    f"Created: {CSS}"
)


app_text = APP.read_text(
    encoding="utf-8"
)


import_line = (
    'import PriorityEngine '
    'from "./components/PriorityEngine";'
)

if import_line not in app_text:
    anchor = (
        'import BuyerPipelineBoard '
        'from "./components/BuyerPipelineBoard";'
    )

    app_text = replace_once(
        app_text,
        anchor,
        import_line
        + "\n"
        + anchor,
        "Priority Engine import",
    )
else:
    print(
        "Priority Engine import already exists."
    )


component_call = (
    "<PriorityEngine "
    "setupRequests={setupRequests} />"
)

if component_call not in app_text:
    revenue_call = (
        "<RevenueCommandCenter />"
    )

    app_text = replace_once(
        app_text,
        revenue_call,
        revenue_call
        + "\n"
        + "      "
        + component_call,
        "Priority Engine cockpit placement",
    )
else:
    print(
        "Priority Engine already inserted."
    )


APP.write_text(
    app_text,
    encoding="utf-8",
)


print()
print("Running frontend build...")


npm_command = (
    "npm.cmd"
    if sys.platform.startswith("win")
    else "npm"
)

result = subprocess.run(
    [
        npm_command,
        "run",
        "build",
    ],
    cwd=FRONTEND,
    text=True,
)

if result.returncode != 0:
    raise SystemExit(
        "Frontend build failed. "
        "Review the TypeScript error above."
    )


print()
print(
    "SUCCESS: WOLF OS PRIORITY ENGINE INSTALLED."
)
print(
    "Revenue Attack Queue now ranks persistent buyer deals."
)
print(
    "Execute Next Move advances the highest-priority target through the SQLite Deal Desk."
)
print(
    "Closing-stage targets copy the close message instead of automatically marking revenue Won."
)
print(
    "Refresh the Owner Console and test TARGET 01."
)