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

COMPONENT = COMPONENTS / "BuyerPipelineBoard.tsx"
CSS = COMPONENTS / "BuyerPipelineBoard.css"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Buyer Pipeline patch starting...")

if not APP.exists():
    raise SystemExit(f"App.tsx not found: {APP}")

COMPONENTS.mkdir(parents=True, exist_ok=True)

backup = APP.with_name(f"App.before-buyer-pipeline-{stamp}.tsx")
shutil.copy2(APP, backup)
print(f"Backup created: {backup}")

component_code = r'''import { useEffect, useMemo, useState } from "react";
import "./BuyerPipelineBoard.css";

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
  phone: string;
  details: string;
  budget: string;
  timeline: string;
};

type Props = {
  setupRequests: unknown[];
};

const STORAGE_KEY = "wolf-os-buyer-pipeline-v1";

const stages: Stage[] = [
  "New",
  "Contacted",
  "Demo",
  "Proposal",
  "Closing",
  "Won",
  "Lost",
];

const stageRank: Record<Stage, number> = {
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
  }).format(Number.isFinite(value) ? value : 0);

function asRecord(value: unknown): Record<string, unknown> {
  if (typeof value === "object" && value !== null) {
    return value as Record<string, unknown>;
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

    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }

    if (typeof value === "number") {
      return String(value);
    }
  }

  return fallback;
}

function defaultDealValue(budget: string) {
  const normalized = budget.replace(/,/g, "");

  if (/5000/i.test(normalized)) return 5000;
  if (/3000/i.test(normalized)) return 3000;
  if (/2500/i.test(normalized)) return 2500;
  if (/1500/i.test(normalized)) return 1500;
  if (/750/i.test(normalized)) return 750;
  if (/499/i.test(normalized)) return 499;
  if (/299/i.test(normalized)) return 299;

  return 1500;
}

function loadPipeline(): Record<string, PipelineState> {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);

    if (!raw) return {};

    return JSON.parse(raw) as Record<string, PipelineState>;
  } catch {
    return {};
  }
}

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

export default function BuyerPipelineBoard({ setupRequests }: Props) {
  const [pipeline, setPipeline] =
    useState<Record<string, PipelineState>>(loadPipeline);
  const [status, setStatus] = useState(
    "Live Buyer Leads loaded into the WOLF OS sales pipeline."
  );
  const [copiedKey, setCopiedKey] = useState("");

  const leads = useMemo<Lead[]>(() => {
    return setupRequests.map((rawLead, index) => {
      const lead = asRecord(rawLead);

      const business = valueText(
        lead,
        ["business_name", "businessName", "business"],
        `Buyer Lead ${index + 1}`
      );

      const name = valueText(
        lead,
        ["name", "contact_name", "contactName"],
        "Buyer"
      );

      const email = valueText(lead, ["email"]);
      const phone = valueText(lead, ["phone", "phone_number"]);
      const details = valueText(
        lead,
        ["what_i_sell", "whatISell", "business_details", "details"],
        "Business setup opportunity"
      );
      const budget = valueText(
        lead,
        ["budget", "package", "package_interest"],
        "Package not selected"
      );
      const timeline = valueText(
        lead,
        ["timeline"],
        "Timeline not selected"
      );

      const id = valueText(lead, ["id", "request_id", "created_at"]);

      return {
        key: id || `${business}-${email || name}-${index}`,
        business,
        name,
        email,
        phone,
        details,
        budget,
        timeline,
      };
    });
  }, [setupRequests]);

  useEffect(() => {
    setPipeline((current) => {
      let changed = false;
      const next = { ...current };

      for (const lead of leads) {
        if (!next[lead.key]) {
          next[lead.key] = {
            stage: "New",
            dealValue: defaultDealValue(lead.budget),
            nextAction: "Contact buyer and schedule live demo",
          };
          changed = true;
        }
      }

      return changed ? next : current;
    });
  }, [leads]);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(pipeline));
  }, [pipeline]);

  const pipelineRows = useMemo(() => {
    return leads
      .map((lead) => ({
        lead,
        deal: pipeline[lead.key] ?? {
          stage: "New" as Stage,
          dealValue: defaultDealValue(lead.budget),
          nextAction: "Contact buyer and schedule live demo",
        },
      }))
      .sort(
        (a, b) =>
          stageRank[b.deal.stage] - stageRank[a.deal.stage] ||
          b.deal.dealValue - a.deal.dealValue
      );
  }, [leads, pipeline]);

  const activePipeline = pipelineRows
    .filter(
      ({ deal }) => deal.stage !== "Won" && deal.stage !== "Lost"
    )
    .reduce((total, { deal }) => total + deal.dealValue, 0);

  const wonRevenue = pipelineRows
    .filter(({ deal }) => deal.stage === "Won")
    .reduce((total, { deal }) => total + deal.dealValue, 0);

  const hotDeals = pipelineRows.filter(({ deal }) =>
    ["Demo", "Proposal", "Closing"].includes(deal.stage)
  ).length;

  const closingRevenue = pipelineRows
    .filter(({ deal }) => deal.stage === "Closing")
    .reduce((total, { deal }) => total + deal.dealValue, 0);

  const updateDeal = (
    key: string,
    update: Partial<PipelineState>
  ) => {
    setPipeline((current) => {
      const existing = current[key] ?? {
        stage: "New",
        dealValue: 1500,
        nextAction: "Contact buyer and schedule live demo",
      };

      return {
        ...current,
        [key]: {
          ...existing,
          ...update,
        },
      };
    });
  };

  const advanceDeal = (key: string, currentStage: Stage) => {
    if (currentStage === "Won" || currentStage === "Lost") {
      setStatus("Closed deals stay locked until you manually change the stage.");
      return;
    }

    const currentIndex = stages.indexOf(currentStage);
    const nextStage = stages[Math.min(currentIndex + 1, 5)];

    updateDeal(key, { stage: nextStage });

    setStatus(`Deal advanced from ${currentStage} to ${nextStage}.`);
  };

  const buildFollowUp = (lead: Lead, deal: PipelineState) =>
    [
      `Hi ${lead.name},`,
      "",
      `Following up about the ${lead.business} storefront and owner system.`,
      "",
      `Based on what you shared â€” ${lead.details} â€” I have the opportunity at the ${deal.stage} stage.`,
      "",
      `Current project direction: ${lead.budget}`,
      `Target project value: ${money(deal.dealValue)}`,
      `Timeline: ${lead.timeline}`,
      "",
      "I can walk you through the live storefront, checkout flow, owner dashboard, orders, inventory, leads, and business intelligence system.",
      "",
      "The next step is confirming the build scope, deposit, and launch timeline.",
      "",
      "Are you ready to move forward?",
      "",
      "Andrew Wolverton",
      "I AM THE ONEâ„¢ Â· WOLF OSâ„¢",
    ].join("\n");

  const copyFollowUp = async (
    lead: Lead,
    deal: PipelineState
  ) => {
    const text = buildFollowUp(lead, deal);

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        copyFallback(text);
      }
    } catch {
      copyFallback(text);
    }

    setCopiedKey(lead.key);
    setStatus(`${lead.business} buyer follow-up copied.`);

    window.setTimeout(() => setCopiedKey(""), 1600);
  };

  const openEmail = (lead: Lead, deal: PipelineState) => {
    if (!lead.email) {
      setStatus(`${lead.business} does not have an email address on the lead.`);
      return;
    }

    const subject = `${lead.business} storefront + owner system`;
    const body = buildFollowUp(lead, deal);

    window.location.href = `mailto:${encodeURIComponent(
      lead.email
    )}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(
      body
    )}`;

    setStatus(`${lead.business} email draft opened.`);
  };

  return (
    <section className="buyer-pipeline-board">
      <header className="buyer-pipeline-header">
        <div>
          <p className="buyer-pipeline-kicker">
            WOLF OSâ„¢ DEAL DESK
          </p>
          <h2>Live Buyer Pipeline</h2>
          <p>
            Turn real setup requests into tracked opportunities, proposals,
            deposits, and won revenue.
          </p>
        </div>

        <div className="buyer-pipeline-live">
          <span />
          {leads.length} LIVE BUYER{leads.length === 1 ? "" : "S"}
        </div>
      </header>

      <div className="buyer-pipeline-metrics">
        <article>
          <span>Active Pipeline</span>
          <strong>{money(activePipeline)}</strong>
          <small>Open buyer opportunities</small>
        </article>

        <article>
          <span>Hot Deals</span>
          <strong>{hotDeals}</strong>
          <small>Demo through closing</small>
        </article>

        <article>
          <span>Closing Revenue</span>
          <strong>{money(closingRevenue)}</strong>
          <small>Deals at final stage</small>
        </article>

        <article className="buyer-pipeline-won">
          <span>Won Revenue</span>
          <strong>{money(wonRevenue)}</strong>
          <small>Closed business</small>
        </article>
      </div>

      <div className="buyer-pipeline-status">{status}</div>

      <div className="buyer-deal-stack">
        {pipelineRows.length === 0 ? (
          <div className="buyer-pipeline-empty">
            No live setup requests yet. New Buyer Leads will automatically
            enter this pipeline.
          </div>
        ) : (
          pipelineRows.map(({ lead, deal }) => (
            <article className="buyer-deal-card" key={lead.key}>
              <div className="buyer-deal-main">
                <div className="buyer-deal-identity">
                  <span className={`buyer-stage stage-${deal.stage.toLowerCase()}`}>
                    {deal.stage}
                  </span>

                  <h3>{lead.business}</h3>

                  <p>
                    {lead.name}
                    {lead.email ? ` Â· ${lead.email}` : ""}
                  </p>
                </div>

                <div className="buyer-deal-value">
                  <span>Deal Value</span>
                  <strong>{money(deal.dealValue)}</strong>
                </div>
              </div>

              <p className="buyer-deal-details">{lead.details}</p>

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
                    value={deal.stage}
                    onChange={(event) =>
                      updateDeal(lead.key, {
                        stage: event.target.value as Stage,
                      })
                    }
                  >
                    {stages.map((stage) => (
                      <option key={stage} value={stage}>
                        {stage}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Deal value
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={deal.dealValue}
                    onChange={(event) =>
                      updateDeal(lead.key, {
                        dealValue: Math.max(
                          0,
                          Number(event.target.value) || 0
                        ),
                      })
                    }
                  />
                </label>

                <label className="buyer-next-action">
                  Next action
                  <input
                    value={deal.nextAction}
                    onChange={(event) =>
                      updateDeal(lead.key, {
                        nextAction: event.target.value,
                      })
                    }
                  />
                </label>
              </div>

              <div className="buyer-deal-actions">
                <button
                  type="button"
                  className="buyer-deal-primary"
                  onClick={() => advanceDeal(lead.key, deal.stage)}
                >
                  Advance Deal
                </button>

                <button
                  type="button"
                  className={
                    copiedKey === lead.key ? "buyer-copied" : ""
                  }
                  onClick={() => copyFollowUp(lead, deal)}
                >
                  {copiedKey === lead.key
                    ? "Follow-up Copied"
                    : "Copy Follow-up"}
                </button>

                <button
                  type="button"
                  onClick={() => openEmail(lead, deal)}
                >
                  Open Buyer Email
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
'''

css_code = r'''.buyer-pipeline-board {
  margin-top: 28px;
  padding: 26px;
  border: 1px solid rgba(77, 255, 169, 0.22);
  border-radius: 24px;
  background:
    radial-gradient(circle at 5% 0%, rgba(0, 255, 157, 0.08), transparent 30%),
    linear-gradient(145deg, rgba(8, 12, 15, 0.98), rgba(3, 5, 7, 0.98));
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
}

.buyer-pipeline-board * {
  box-sizing: border-box;
}

.buyer-pipeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.buyer-pipeline-kicker {
  margin: 0 0 7px;
  color: #68ffb2;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.17em;
  text-transform: uppercase;
}

.buyer-pipeline-header h2 {
  margin: 0;
  color: #fff;
  font-size: clamp(1.55rem, 3vw, 2.35rem);
  letter-spacing: -0.04em;
}

.buyer-pipeline-header p {
  max-width: 720px;
  margin: 9px 0 0;
  color: rgba(235, 241, 248, 0.64);
  line-height: 1.55;
}

.buyer-pipeline-live {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 9px;
  padding: 10px 13px;
  border: 1px solid rgba(76, 255, 166, 0.27);
  border-radius: 999px;
  background: rgba(23, 117, 73, 0.14);
  color: #6dffb1;
  font-size: 0.72rem;
  font-weight: 900;
}

.buyer-pipeline-live span {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #55ffa0;
  box-shadow: 0 0 15px #55ffa0;
}

.buyer-pipeline-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.buyer-pipeline-metrics article {
  min-height: 125px;
  padding: 17px;
  border: 1px solid rgba(255, 255, 255, 0.075);
  border-radius: 17px;
  background: rgba(255, 255, 255, 0.025);
}

.buyer-pipeline-metrics article > span,
.buyer-deal-value span {
  color: rgba(235, 242, 249, 0.54);
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.buyer-pipeline-metrics strong {
  display: block;
  margin-top: 12px;
  color: #fff;
  font-size: clamp(1.4rem, 2.5vw, 2rem);
}

.buyer-pipeline-metrics small {
  display: block;
  margin-top: 9px;
  color: rgba(228, 235, 242, 0.47);
}

.buyer-pipeline-metrics .buyer-pipeline-won {
  border-color: rgba(76, 255, 166, 0.28);
  background: rgba(38, 139, 88, 0.11);
}

.buyer-pipeline-won strong {
  color: #72ffb5;
}

.buyer-pipeline-status {
  margin: 14px 0;
  padding: 11px 14px;
  border-left: 3px solid #5affaa;
  border-radius: 8px;
  background: rgba(64, 255, 160, 0.055);
  color: rgba(230, 244, 237, 0.69);
  font-size: 0.82rem;
}

.buyer-deal-stack {
  display: grid;
  gap: 13px;
}

.buyer-deal-card {
  padding: 19px;
  border: 1px solid rgba(255, 255, 255, 0.075);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.042), rgba(255, 255, 255, 0.012));
}

.buyer-deal-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.buyer-stage {
  display: inline-flex;
  padding: 6px 9px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 0.66rem;
  font-weight: 900;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.stage-demo,
.stage-proposal,
.stage-closing {
  border-color: rgba(255, 177, 52, 0.4);
  background: rgba(255, 137, 0, 0.11);
  color: #ffc15f;
}

.stage-won {
  border-color: rgba(74, 255, 163, 0.4);
  background: rgba(35, 169, 98, 0.13);
  color: #6fffb1;
}

.stage-lost {
  border-color: rgba(255, 90, 90, 0.3);
  background: rgba(164, 38, 38, 0.12);
  color: #ff8c8c;
}

.buyer-deal-identity h3 {
  margin: 11px 0 0;
  color: #fff;
  font-size: 1.14rem;
}

.buyer-deal-identity p {
  margin: 5px 0 0;
  color: rgba(234, 240, 247, 0.52);
  font-size: 0.8rem;
}

.buyer-deal-value {
  text-align: right;
}

.buyer-deal-value strong {
  display: block;
  margin-top: 7px;
  color: #72ffb5;
  font-size: 1.55rem;
}

.buyer-deal-details {
  margin: 15px 0;
  color: rgba(239, 244, 249, 0.69);
  line-height: 1.55;
}

.buyer-deal-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.buyer-deal-meta span {
  padding: 8px 10px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 9px;
  background: rgba(0, 0, 0, 0.18);
  color: rgba(235, 241, 248, 0.62);
  font-size: 0.73rem;
}

.buyer-deal-meta b {
  margin-right: 7px;
  color: #fff;
}

.buyer-deal-controls {
  display: grid;
  grid-template-columns: 0.7fr 0.7fr 1.6fr;
  gap: 10px;
  margin-top: 16px;
}

.buyer-deal-controls label {
  color: rgba(232, 239, 246, 0.57);
  font-size: 0.72rem;
  font-weight: 800;
}

.buyer-deal-controls input,
.buyer-deal-controls select {
  width: 100%;
  margin-top: 7px;
  padding: 11px 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  outline: none;
  background: rgba(0, 0, 0, 0.28);
  color: #fff;
  font: inherit;
}

.buyer-deal-controls select option {
  background: #0a0d10;
  color: #fff;
}

.buyer-deal-controls input:focus,
.buyer-deal-controls select:focus {
  border-color: rgba(89, 255, 172, 0.5);
  box-shadow: 0 0 0 3px rgba(70, 255, 160, 0.07);
}

.buyer-deal-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.buyer-deal-actions button {
  padding: 10px 13px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 900;
  cursor: pointer;
}

.buyer-deal-actions .buyer-deal-primary {
  border-color: #55ffa5;
  background: linear-gradient(135deg, #42e98c, #7affb9);
  color: #03140a;
}

.buyer-deal-actions .buyer-copied {
  border-color: rgba(86, 255, 171, 0.55);
  background: rgba(48, 155, 96, 0.19);
  color: #76ffb6;
}

.buyer-pipeline-empty {
  padding: 35px;
  border: 1px dashed rgba(255, 255, 255, 0.13);
  border-radius: 16px;
  color: rgba(233, 240, 247, 0.55);
  text-align: center;
}

@media (max-width: 1000px) {
  .buyer-pipeline-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .buyer-deal-controls {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .buyer-next-action {
    grid-column: 1 / -1;
  }
}

@media (max-width: 680px) {
  .buyer-pipeline-board {
    padding: 18px;
  }

  .buyer-pipeline-header,
  .buyer-deal-main {
    align-items: flex-start;
    flex-direction: column;
  }

  .buyer-pipeline-metrics,
  .buyer-deal-controls {
    grid-template-columns: 1fr;
  }

  .buyer-next-action {
    grid-column: auto;
  }

  .buyer-deal-value {
    text-align: left;
  }

  .buyer-deal-actions,
  .buyer-deal-actions button {
    width: 100%;
  }
}
'''

COMPONENT.write_text(component_code, encoding="utf-8")
CSS.write_text(css_code, encoding="utf-8")

print(f"Created: {COMPONENT}")
print(f"Created: {CSS}")

app_text = APP.read_text(encoding="utf-8")

import_line = 'import BuyerPipelineBoard from "./components/BuyerPipelineBoard";'

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

    print("Added BuyerPipelineBoard import.")
else:
    print("BuyerPipelineBoard import already exists.")

if "<BuyerPipelineBoard" not in app_text:
    revenue_match = re.search(
        r"<RevenueCommandCenter\s*/>",
        app_text,
    )

    if revenue_match is None:
        raise SystemExit(
            "RevenueCommandCenter call not found. "
            f"App.tsx backup remains at: {backup}"
        )

    line_start = app_text.rfind("\n", 0, revenue_match.start()) + 1
    indent_match = re.match(
        r"[ \t]*",
        app_text[line_start:revenue_match.start()],
    )
    indentation = indent_match.group(0) if indent_match else ""

    position = revenue_match.end()

    app_text = (
        app_text[:position]
        + "\n"
        + indentation
        + "<BuyerPipelineBoard setupRequests={setupRequests} />"
        + app_text[position:]
    )

    print("Inserted live Buyer Pipeline beneath Revenue Command Center.")
else:
    print("Buyer Pipeline already inserted.")

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
        f"Backup: {backup}"
    )

print()
print("SUCCESS: LIVE BUYER PIPELINE INSTALLED.")
print("The 3 real Buyer Leads now feed the WOLF OS Deal Desk.")
print("Test: Advance Deal, change Deal Value, enter Next Action, copy follow-up.")
