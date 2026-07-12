from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
SRC = FRONTEND / "src"
COMPONENTS = SRC / "components"
LIB = SRC / "lib"

BACKEND_APP = BACKEND / "app" / "__init__.py"
DB = BACKEND / "data" / "i_am_the_one_saas.sqlite3"

PIPELINE_STORE = LIB / "pipelineState.ts"
BUYER_PIPELINE = COMPONENTS / "BuyerPipelineBoard.tsx"
REVENUE = COMPONENTS / "RevenueCommandCenter.tsx"
PRIORITY = COMPONENTS / "PriorityEngine.tsx"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS UNIFIED PIPELINE STATE REPAIR starting...")


def backup(path: Path, name: str) -> None:
    backup_dir = ROOT / "backups" / "unified-pipeline-state"

    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = backup_dir / (
        f"{name}-{stamp}{path.suffix}"
    )

    shutil.copy2(
        path,
        target,
    )

    print(f"Backup created: {target}")


def require(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            f"Required file not found: {path}"
        )


for path in [
    BACKEND_APP,
    BUYER_PIPELINE,
    REVENUE,
    PRIORITY,
]:
    require(path)


LIB.mkdir(
    parents=True,
    exist_ok=True,
)


backup(
    BACKEND_APP,
    "backend-init",
)

backup(
    BUYER_PIPELINE,
    "BuyerPipelineBoard",
)

backup(
    REVENUE,
    "RevenueCommandCenter",
)

backup(
    PRIORITY,
    "PriorityEngine",
)


if DB.exists():
    backup(
        DB,
        "database",
    )


print()
print("--- PATCHING SQLITE PIPELINE AUTHORITY ---")


backend = BACKEND_APP.read_text(
    encoding="utf-8"
)


schema_code = '''        con.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_deals (
                lead_id TEXT PRIMARY KEY,
                stage TEXT NOT NULL DEFAULT 'New',
                deal_value INTEGER NOT NULL DEFAULT 0,
                next_action TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_activity (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        con.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_pipeline_activity_lead_created
            ON pipeline_activity (
                lead_id,
                created_at DESC
            )
            """
        )

'''


if (
    "CREATE TABLE IF NOT EXISTS pipeline_deals"
    not in backend
    or "CREATE TABLE IF NOT EXISTS pipeline_activity"
    not in backend
):
    anchor = "        for name, ddl in {"

    position = backend.find(anchor)

    if position < 0:
        raise SystemExit(
            "Schema anchor not found."
        )

    backend = (
        backend[:position]
        + schema_code
        + backend[position:]
    )

    print(
        "Ensured pipeline SQLite schema."
    )
else:
    print(
        "Pipeline SQLite schema already present."
    )


unified_routes = '''    @app.get("/api/owner/pipeline-state")
    def owner_unified_pipeline_state():
        ok, error = require_owner()

        if not ok:
            return error

        con = connect(app)

        try:
            rows = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                FROM pipeline_deals
                ORDER BY updated_at DESC
                """
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "count": len(rows),
                    "pipeline_deals": [
                        dict(row)
                        for row in rows
                    ],
                }
            )

        finally:
            con.close()

    @app.put("/api/owner/pipeline-state/<lead_id>")
    def owner_update_unified_pipeline_state(
        lead_id: str
    ):
        ok, error = require_owner()

        if not ok:
            return error

        payload = request.get_json(
            silent=True
        ) or {}

        allowed_stages = {
            "New",
            "Contacted",
            "Demo",
            "Proposal",
            "Closing",
            "Won",
            "Lost",
        }

        stage = str(
            payload.get("stage") or "New"
        ).strip()

        if stage not in allowed_stages:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        f"Invalid pipeline stage: {stage}"
                    ),
                }
            ), 400

        try:
            deal_value = int(
                float(
                    payload.get(
                        "deal_value",
                        0,
                    )
                    or 0
                )
            )

        except (TypeError, ValueError):
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "deal_value must be numeric."
                    ),
                }
            ), 400

        deal_value = max(
            0,
            deal_value,
        )

        next_action = str(
            payload.get("next_action") or ""
        ).strip()

        con = connect(app)

        try:
            lead = con.execute(
                """
                SELECT
                    id,
                    business_name
                FROM setup_requests
                WHERE id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            if not lead:
                return jsonify(
                    {
                        "ok": False,
                        "error": "Buyer lead not found.",
                    }
                ), 404

            existing = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action
                FROM pipeline_deals
                WHERE lead_id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            updated_at = now_iso()

            changes = []

            if existing:
                old_stage = str(
                    existing["stage"] or ""
                )

                old_value = int(
                    existing["deal_value"] or 0
                )

                old_action = str(
                    existing["next_action"] or ""
                )

                if old_stage != stage:
                    changes.append(
                        (
                            "stage_changed",
                            old_stage,
                            stage,
                            (
                                "Stage moved from "
                                f"{old_stage} to {stage}."
                            ),
                        )
                    )

                if old_value != deal_value:
                    changes.append(
                        (
                            "deal_value_changed",
                            str(old_value),
                            str(deal_value),
                            (
                                "Deal value changed from "
                                f"${old_value:,} "
                                f"to ${deal_value:,}."
                            ),
                        )
                    )

                if old_action != next_action:
                    changes.append(
                        (
                            "next_action_changed",
                            old_action,
                            next_action,
                            "Next action updated.",
                        )
                    )

            else:
                changes.append(
                    (
                        "deal_created",
                        "",
                        stage,
                        (
                            "Deal entered the pipeline at "
                            f"{stage} with a "
                            f"${deal_value:,} value."
                        ),
                    )
                )

            con.execute(
                """
                INSERT INTO pipeline_deals (
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(lead_id)
                DO UPDATE SET
                    stage = excluded.stage,
                    deal_value = excluded.deal_value,
                    next_action = excluded.next_action,
                    updated_at = excluded.updated_at
                """,
                (
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at,
                ),
            )

            for (
                activity_type,
                old_value,
                new_value,
                summary,
            ) in changes:
                con.execute(
                    """
                    INSERT INTO pipeline_activity (
                        id,
                        lead_id,
                        activity_type,
                        old_value,
                        new_value,
                        summary,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id("ACT"),
                        lead_id,
                        activity_type,
                        old_value,
                        new_value,
                        summary,
                        updated_at,
                    ),
                )

            con.commit()

            deal = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                FROM pipeline_deals
                WHERE lead_id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            snapshot = con.execute(
                """
                SELECT
                    lead_id,
                    stage,
                    deal_value,
                    next_action,
                    updated_at
                FROM pipeline_deals
                ORDER BY updated_at DESC
                """
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "deal": dict(deal),
                    "activities_written": len(changes),
                    "pipeline_deals": [
                        dict(row)
                        for row in snapshot
                    ],
                }
            )

        except Exception as exc:
            con.rollback()

            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Unified pipeline update failed: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                }
            ), 500

        finally:
            con.close()

'''


if (
    '@app.get("/api/owner/pipeline-state")'
    not in backend
):
    anchor = (
        '    @app.post("/api/owner/login")'
    )

    position = backend.find(anchor)

    if position < 0:
        raise SystemExit(
            "Owner login route anchor not found."
        )

    backend = (
        backend[:position]
        + unified_routes
        + backend[position:]
    )

    print(
        "Added unified SQLite pipeline endpoints."
    )
else:
    print(
        "Unified pipeline endpoints already present."
    )


BACKEND_APP.write_text(
    backend,
    encoding="utf-8",
)


print()
print("--- CREATING SHARED PIPELINE STATE LAYER ---")


pipeline_store_code = r'''import {
  useCallback,
  useEffect,
  useState,
} from "react";

export type PipelineStage =
  | "New"
  | "Contacted"
  | "Demo"
  | "Proposal"
  | "Closing"
  | "Won"
  | "Lost";

export type PipelineState = {
  stage: PipelineStage;
  dealValue: number;
  nextAction: string;
};

export type PipelineMap = Record<
  string,
  PipelineState
>;

type RemoteDeal = {
  lead_id?: unknown;
  stage?: unknown;
  deal_value?: unknown;
  next_action?: unknown;
};

type UnifiedPipelineEventDetail = {
  pipeline: PipelineMap;
};

const API_BASE = String(
  import.meta.env.VITE_BACKEND_URL ||
    "http://127.0.0.1:5000"
).replace(/\/+$/, "");

export const PIPELINE_STORAGE_KEY =
  "wolf-os-buyer-pipeline-v2";

export const PIPELINE_STATE_EVENT =
  "wolf-os-unified-pipeline-updated";

export const PIPELINE_ACTIVITY_EVENT =
  "wolf-os-pipeline-activity-updated";

const stages: PipelineStage[] = [
  "New",
  "Contacted",
  "Demo",
  "Proposal",
  "Closing",
  "Won",
  "Lost",
];

function resolveOwnerToken(
  ownerToken = ""
) {
  return (
    ownerToken ||
    window.localStorage.getItem(
      "wolf_owner_token"
    ) ||
    ""
  );
}

function isStage(
  value: unknown
): value is PipelineStage {
  return (
    typeof value === "string" &&
    stages.includes(
      value as PipelineStage
    )
  );
}

function normalizePipeline(
  rows: unknown
): PipelineMap {
  const pipeline: PipelineMap = {};

  if (!Array.isArray(rows)) {
    return pipeline;
  }

  for (const raw of rows) {
    if (
      typeof raw !== "object" ||
      raw === null
    ) {
      continue;
    }

    const row =
      raw as RemoteDeal;

    const leadId = String(
      row.lead_id || ""
    ).trim();

    if (!leadId) {
      continue;
    }

    pipeline[leadId] = {
      stage: isStage(row.stage)
        ? row.stage
        : "New",
      dealValue: Math.max(
        0,
        Number(row.deal_value) || 0
      ),
      nextAction: String(
        row.next_action || ""
      ),
    };
  }

  return pipeline;
}

export function readPipelineCache():
  PipelineMap {
  try {
    const raw =
      window.localStorage.getItem(
        PIPELINE_STORAGE_KEY
      );

    if (!raw) {
      return {};
    }

    return JSON.parse(
      raw
    ) as PipelineMap;

  } catch {
    return {};
  }
}

function publishPipeline(
  pipeline: PipelineMap
) {
  window.localStorage.setItem(
    PIPELINE_STORAGE_KEY,
    JSON.stringify(pipeline)
  );

  window.dispatchEvent(
    new CustomEvent<UnifiedPipelineEventDetail>(
      PIPELINE_STATE_EVENT,
      {
        detail: {
          pipeline,
        },
      }
    )
  );
}

export async function fetchUnifiedPipeline(
  ownerToken = ""
): Promise<PipelineMap> {
  const token =
    resolveOwnerToken(ownerToken);

  if (!token) {
    throw new Error(
      "Owner token is not available."
    );
  }

  const response = await fetch(
    `${API_BASE}/api/owner/pipeline-state`,
    {
      headers: {
        Authorization:
          `Bearer ${token}`,
      },
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
        `Pipeline load failed: ${response.status}`
    );
  }

  const pipeline =
    normalizePipeline(
      payload.pipeline_deals
    );

  publishPipeline(pipeline);

  return pipeline;
}

export async function saveUnifiedPipelineDeal(
  leadId: string,
  deal: PipelineState,
  ownerToken = ""
): Promise<PipelineMap> {
  const token =
    resolveOwnerToken(ownerToken);

  if (!token) {
    throw new Error(
      "Owner token is not available."
    );
  }

  const response = await fetch(
    `${API_BASE}/api/owner/pipeline-state/${encodeURIComponent(
      leadId
    )}`,
    {
      method: "PUT",
      headers: {
        Authorization:
          `Bearer ${token}`,
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        stage: deal.stage,
        deal_value:
          deal.dealValue,
        next_action:
          deal.nextAction,
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
        `Pipeline save failed: ${response.status}`
    );
  }

  const pipeline =
    normalizePipeline(
      payload.pipeline_deals
    );

  publishPipeline(pipeline);

  window.dispatchEvent(
    new CustomEvent(
      PIPELINE_ACTIVITY_EVENT
    )
  );

  return pipeline;
}

export function useUnifiedPipeline(
  ownerToken = ""
) {
  const [pipeline, setPipeline] =
    useState<PipelineMap>(
      readPipelineCache
    );

  const [
    pipelineStatus,
    setPipelineStatus,
  ] = useState(
    "Connecting to unified SQLite pipeline..."
  );

  const [
    pipelineReady,
    setPipelineReady,
  ] = useState(false);

  const refreshPipeline =
    useCallback(async () => {
      try {
        const next =
          await fetchUnifiedPipeline(
            ownerToken
          );

        setPipeline(next);

        setPipelineReady(true);

        setPipelineStatus(
          `${Object.keys(next).length} deals synchronized from SQLite.`
        );

        return next;

      } catch (error) {
        setPipelineReady(false);

        setPipelineStatus(
          error instanceof Error
            ? `Pipeline sync error: ${error.message}`
            : "Pipeline synchronization failed."
        );

        throw error;
      }
    }, [ownerToken]);

  useEffect(() => {
    const onPipelineUpdate = (
      event: Event
    ) => {
      const detail = (
        event as CustomEvent<
          UnifiedPipelineEventDetail
        >
      ).detail;

      if (detail?.pipeline) {
        setPipeline(
          detail.pipeline
        );

        setPipelineReady(true);

        setPipelineStatus(
          `${Object.keys(detail.pipeline).length} deals synchronized from SQLite.`
        );

        return;
      }

      setPipeline(
        readPipelineCache()
      );
    };

    const onStorage = (
      event: StorageEvent
    ) => {
      if (
        event.key ===
        PIPELINE_STORAGE_KEY
      ) {
        setPipeline(
          readPipelineCache()
        );
      }
    };

    window.addEventListener(
      PIPELINE_STATE_EVENT,
      onPipelineUpdate
    );

    window.addEventListener(
      "storage",
      onStorage
    );

    void refreshPipeline().catch(
      () => {
        return;
      }
    );

    return () => {
      window.removeEventListener(
        PIPELINE_STATE_EVENT,
        onPipelineUpdate
      );

      window.removeEventListener(
        "storage",
        onStorage
      );
    };
  }, [refreshPipeline]);

  return {
    pipeline,
    pipelineReady,
    pipelineStatus,
    refreshPipeline,
  };
}
'''


PIPELINE_STORE.write_text(
    pipeline_store_code,
    encoding="utf-8",
)

print(
    f"Created shared state layer: {PIPELINE_STORE}"
)


print()
print("--- REWRITING DEAL DESK ---")


buyer_pipeline_code = r'''import {
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
'''


BUYER_PIPELINE.write_text(
    buyer_pipeline_code,
    encoding="utf-8",
)

print(
    "Deal Desk now reads and writes unified SQLite state."
)


print()
print("--- REWRITING REVENUE ENGINE ---")


revenue_code = r'''import {
  useMemo,
  useState,
} from "react";

import {
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
    Object.values(pipeline);

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
'''


REVENUE.write_text(
    revenue_code,
    encoding="utf-8",
)

print(
    "Revenue Engine now calculates from unified SQLite state."
)


print()
print("--- REWRITING PRIORITY ENGINE STATE CONNECTION ---")


priority = PRIORITY.read_text(
    encoding="utf-8"
)


old_import = '''import { useEffect, useMemo, useRef, useState } from "react";
import "./PriorityEngine.css";'''

new_import = '''import { useEffect, useMemo, useRef, useState } from "react";

import {
  type PipelineState,
  saveUnifiedPipelineDeal,
  useUnifiedPipeline,
} from "../lib/pipelineState";

import "./PriorityEngine.css";'''


if old_import not in priority:
    raise SystemExit(
        "Priority Engine import anchor not found."
    )


priority = priority.replace(
    old_import,
    new_import,
    1,
)


old_pipeline_type = '''type PipelineState = {
  stage: Stage;
  dealValue: number;
  nextAction: string;
};

'''

priority = priority.replace(
    old_pipeline_type,
    "",
    1,
)


old_storage_constants = '''const STORAGE_KEY =
  "wolf-os-buyer-pipeline-v2";

const PIPELINE_EVENT =
  "wolf-os-pipeline-updated";

const ACTIVITY_EVENT =
  "wolf-os-pipeline-activity-updated";

const API_BASE = String(
  import.meta.env.VITE_BACKEND_URL ||
    "http://127.0.0.1:5000"
).replace(/\\/+$/, "");

'''

priority = priority.replace(
    old_storage_constants,
    "",
    1,
)


load_start = '''function loadPipeline(): Record<
  string,
  PipelineState
> {
'''

load_position = priority.find(
    load_start
)

if load_position < 0:
    raise SystemExit(
        "Priority Engine loadPipeline start not found."
    )


copy_position = priority.find(
    "function copyFallback(",
    load_position,
)

if copy_position < 0:
    raise SystemExit(
        "Priority Engine copyFallback anchor not found."
    )


priority = (
    priority[:load_position]
    + priority[copy_position:]
)


old_pipeline_state = '''  const [pipeline, setPipeline] =
    useState<
      Record<string, PipelineState>
    >(loadPipeline);

  const [status, setStatus] =
'''

new_pipeline_state = '''  const {
    pipeline,
    pipelineStatus,
  } = useUnifiedPipeline();

  const [status, setStatus] =
'''


if old_pipeline_state not in priority:
    raise SystemExit(
        "Priority Engine pipeline state anchor not found."
    )


priority = priority.replace(
    old_pipeline_state,
    new_pipeline_state,
    1,
)


sync_start = '''  useEffect(() => {
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

'''


if sync_start not in priority:
    raise SystemExit(
        "Priority Engine local sync effect not found."
    )


priority = priority.replace(
    sync_start,
    "",
    1,
)


fetch_start = '''      try {
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
'''


fetch_replacement = '''      try {
        await saveUnifiedPipelineDeal(
          target.lead.key,
          nextDeal,
          ownerToken
        );

        showFeedback(
'''


if fetch_start not in priority:
    raise SystemExit(
        "Priority Engine execution fetch block not found."
    )


priority = priority.replace(
    fetch_start,
    fetch_replacement,
    1,
)


old_status_footer = '''          {status}
        </p>
      </footer>'''


new_status_footer = '''          {status}
          {" · "}
          {pipelineStatus}
        </p>
      </footer>'''


if old_status_footer not in priority:
    raise SystemExit(
        "Priority Engine status footer not found."
    )


priority = priority.replace(
    old_status_footer,
    new_status_footer,
    1,
)


PRIORITY.write_text(
    priority,
    encoding="utf-8",
)

print(
    "Priority Engine now saves through unified SQLite state."
)


print()
print("--- MOVING BUILD BACKUPS OUT OF FRONTEND SRC ---")


backup_dir = (
    ROOT
    / "backups"
    / "typescript-src-backups"
)

backup_dir.mkdir(
    parents=True,
    exist_ok=True,
)

moved = 0

for path in list(
    SRC.rglob("*.tsx")
):
    if ".before-" not in path.name:
        continue

    relative = str(
        path.relative_to(SRC)
    ).replace(
        "\\",
        "__",
    ).replace(
        "/",
        "__",
    )

    target = (
        backup_dir
        / f"{stamp}-{relative}"
    )

    shutil.move(
        str(path),
        str(target),
    )

    print(
        f"Moved build backup: {path.name}"
    )

    moved += 1


print(
    f"Moved {moved} TSX backup file(s) out of src."
)


print()
print("--- VERIFYING FLASK ROUTES ---")


backend_python = (
    BACKEND
    / ".venv"
    / "Scripts"
    / "python.exe"
)


route_check = subprocess.run(
    [
        str(backend_python),
        "-c",
        (
            "import wsgi; "
            "rules={str(r):sorted(r.methods) "
            "for r in wsgi.app.url_map.iter_rules()}; "
            "assert '/api/owner/pipeline-state' in rules; "
            "assert 'GET' in rules['/api/owner/pipeline-state']; "
            "assert '/api/owner/pipeline-state/<lead_id>' in rules; "
            "assert 'PUT' in rules['/api/owner/pipeline-state/<lead_id>']; "
            "assert '/api/owner/pipeline-activity' in rules; "
            "print('UNIFIED PIPELINE ROUTES OK'); "
            "print('/api/owner/pipeline-state', "
            "rules['/api/owner/pipeline-state']); "
            "print('/api/owner/pipeline-state/<lead_id>', "
            "rules['/api/owner/pipeline-state/<lead_id>']); "
            "print('/api/owner/pipeline-activity', "
            "rules['/api/owner/pipeline-activity'])"
        ),
    ],
    cwd=BACKEND,
    text=True,
)


if route_check.returncode != 0:
    raise SystemExit(
        "Unified Flask route verification failed."
    )


print()
print("--- RUNNING FRONTEND BUILD ---")


npm_command = (
    "npm.cmd"
    if sys.platform.startswith("win")
    else "npm"
)


build = subprocess.run(
    [
        npm_command,
        "run",
        "build",
    ],
    cwd=FRONTEND,
    text=True,
)


if build.returncode != 0:
    raise SystemExit(
        "Frontend build failed. Review the TypeScript error above."
    )


print()
print(
    "SUCCESS: WOLF OS UNIFIED PIPELINE STATE INSTALLED."
)

print(
    "SQLite is now the single pipeline authority."
)

print(
    "Priority Engine, Deal Desk, and Revenue Engine share one synchronized state layer."
)

print(
    "Unified PUT updates now write audit history and return the full SQLite pipeline snapshot."
)

print(
    "Deal value and next-action inputs now save on blur instead of creating an audit record for every keystroke."
)

print(
    "Restart backend and frontend before testing."
)