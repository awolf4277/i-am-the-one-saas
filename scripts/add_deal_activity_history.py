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

BACKEND_APP = BACKEND / "app" / "__init__.py"
PIPELINE = COMPONENTS / "BuyerPipelineBoard.tsx"
APP = SRC / "App.tsx"

ACTIVITY_COMPONENT = COMPONENTS / "DealActivityTimeline.tsx"
ACTIVITY_CSS = COMPONENTS / "DealActivityTimeline.css"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Deal Activity Audit Trail patch starting...")


def backup(path: Path, label: str) -> Path:
    backup_dir = ROOT / "backups" / "deal-activity"
    backup_dir.mkdir(parents=True, exist_ok=True)

    target = backup_dir / (
        f"{path.stem}-{label}-{stamp}{path.suffix}"
    )

    shutil.copy2(path, target)

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

    return text.replace(old, new, 1)


for path in [
    BACKEND_APP,
    PIPELINE,
    APP,
]:
    if not path.exists():
        raise SystemExit(
            f"Required file not found: {path}"
        )


backup(BACKEND_APP, "before-audit")
backup(PIPELINE, "before-audit")
backup(APP, "before-audit")


backend = BACKEND_APP.read_text(
    encoding="utf-8"
)


schema_code = '''        con.execute(
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
    "CREATE TABLE IF NOT EXISTS pipeline_activity"
    not in backend
):
    schema_anchor = "        for name, ddl in {"

    position = backend.find(schema_anchor)

    if position < 0:
        raise SystemExit(
            "PATCH STOPPED: Schema anchor not found."
        )

    backend = (
        backend[:position]
        + schema_code
        + backend[position:]
    )

    print(
        "Added pipeline_activity SQLite table."
    )
else:
    print(
        "pipeline_activity table already defined."
    )


activity_route = '''    @app.get("/api/owner/pipeline/activity")
    def owner_pipeline_activity():
        ok, error = require_owner()

        if not ok:
            return error

        lead_id = str(
            request.args.get("lead_id") or ""
        ).strip()

        try:
            limit = int(
                request.args.get("limit") or 50
            )
        except (TypeError, ValueError):
            limit = 50

        limit = max(
            1,
            min(limit, 200),
        )

        con = connect(app)

        try:
            params = []

            sql = """
                SELECT
                    pa.id,
                    pa.lead_id,
                    pa.activity_type,
                    pa.old_value,
                    pa.new_value,
                    pa.summary,
                    pa.created_at,
                    sr.business_name,
                    sr.name,
                    sr.email
                FROM pipeline_activity pa
                LEFT JOIN setup_requests sr
                    ON sr.id = pa.lead_id
            """

            if lead_id:
                sql += """
                    WHERE pa.lead_id = ?
                """

                params.append(lead_id)

            sql += """
                ORDER BY pa.created_at DESC
                LIMIT ?
            """

            params.append(limit)

            rows = con.execute(
                sql,
                tuple(params),
            ).fetchall()

            return jsonify(
                {
                    "ok": True,
                    "count": len(rows),
                    "activities": [
                        dict(row)
                        for row in rows
                    ],
                }
            )

        finally:
            con.close()

'''


if (
    '@app.get("/api/owner/pipeline/activity")'
    not in backend
):
    route_anchor = (
        '    @app.get("/api/owner/pipeline")'
    )

    position = backend.find(route_anchor)

    if position < 0:
        raise SystemExit(
            "PATCH STOPPED: Pipeline route anchor not found."
        )

    backend = (
        backend[:position]
        + activity_route
        + backend[position:]
    )

    print(
        "Added owner pipeline activity API."
    )
else:
    print(
        "Pipeline activity API already exists."
    )


old_existing = '''            existing = con.execute(
                """
                SELECT lead_id
                FROM pipeline_deals
                WHERE lead_id = ?
                LIMIT 1
                """,
                (lead_id,),
            ).fetchone()

            if existing:
'''

new_existing = '''            existing = con.execute(
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

            activity_items = []

            if existing:
                if str(existing["stage"]) != stage:
                    activity_items.append(
                        (
                            "stage_changed",
                            str(existing["stage"]),
                            stage,
                            (
                                "Stage moved from "
                                f"{existing['stage']} to {stage}."
                            ),
                        )
                    )

                if int(existing["deal_value"]) != deal_value:
                    activity_items.append(
                        (
                            "deal_value_changed",
                            str(existing["deal_value"]),
                            str(deal_value),
                            (
                                "Deal value changed from "
                                f"${int(existing['deal_value']):,} "
                                f"to ${deal_value:,}."
                            ),
                        )
                    )

                if str(existing["next_action"]) != next_action:
                    activity_items.append(
                        (
                            "next_action_changed",
                            str(existing["next_action"]),
                            next_action,
                            "Next action updated.",
                        )
                    )

            else:
                activity_items.append(
                    (
                        "deal_created",
                        "",
                        stage,
                        (
                            "Deal entered the pipeline at "
                            f"{stage} with a ${deal_value:,} value."
                        ),
                    )
                )

            if existing:
'''

backend = replace_once(
    backend,
    old_existing,
    new_existing,
    "pipeline activity change detection",
)


old_commit = '''            con.commit()

            row = con.execute(
'''

new_commit = '''            for (
                activity_type,
                old_value,
                new_value,
                summary,
            ) in activity_items:
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

            row = con.execute(
'''

backend = replace_once(
    backend,
    old_commit,
    new_commit,
    "pipeline activity recording",
)


BACKEND_APP.write_text(
    backend,
    encoding="utf-8",
)

print(
    "Backend now records Deal Desk history."
)


pipeline = PIPELINE.read_text(
    encoding="utf-8"
)


old_save = '''      await saveDealRemote(
        leadId,
        deal
      );

      setStatus(
        "Deal saved to the WOLF OS SQLite backend."
      );
'''

new_save = '''      await saveDealRemote(
        leadId,
        deal
      );

      window.dispatchEvent(
        new CustomEvent(
          "wolf-os-pipeline-activity-updated"
        )
      );

      setStatus(
        "Deal saved to the WOLF OS SQLite backend."
      );
'''

pipeline = replace_once(
    pipeline,
    old_save,
    new_save,
    "Deal Desk activity refresh signal",
)


PIPELINE.write_text(
    pipeline,
    encoding="utf-8",
)


activity_component_code = r'''import { useCallback, useEffect, useState } from "react";
import "./DealActivityTimeline.css";

type Activity = {
  id: string;
  leadId: string;
  activityType: string;
  oldValue: string;
  newValue: string;
  summary: string;
  createdAt: string;
  businessName: string;
  contactName: string;
  email: string;
};

const API_BASE = String(
  import.meta.env.VITE_BACKEND_URL ||
    "http://127.0.0.1:5000"
).replace(/\/+$/, "");

function asRecord(
  value: unknown
): Record<string, unknown> {
  if (
    typeof value === "object" &&
    value !== null
  ) {
    return value as Record<string, unknown>;
  }

  return {};
}

function text(
  record: Record<string, unknown>,
  key: string
) {
  const value = record[key];

  if (
    typeof value === "string" ||
    typeof value === "number"
  ) {
    return String(value);
  }

  return "";
}

function formatActivityTime(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function activityLabel(type: string) {
  switch (type) {
    case "deal_created":
      return "Deal Created";

    case "stage_changed":
      return "Stage Change";

    case "deal_value_changed":
      return "Value Change";

    case "next_action_changed":
      return "Next Action";

    default:
      return "Deal Activity";
  }
}

export default function DealActivityTimeline() {
  const [activities, setActivities] = useState<
    Activity[]
  >([]);

  const [status, setStatus] = useState(
    "Loading persistent deal activity..."
  );

  const loadActivity = useCallback(async () => {
    const ownerToken =
      window.localStorage.getItem(
        "wolf_owner_token"
      ) || "";

    if (!ownerToken) {
      setStatus(
        "Unlock Owner Console to load Deal Desk activity."
      );

      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/owner/pipeline/activity?limit=40`,
        {
          headers: {
            Authorization:
              `Bearer ${ownerToken}`,
          },
        }
      );

      const payload = await response.json();

      if (!response.ok || !payload?.ok) {
        throw new Error(
          payload?.error ||
            `Activity load failed: ${response.status}`
        );
      }

      const rows = Array.isArray(
        payload.activities
      )
        ? payload.activities
        : [];

      const nextActivities =
        rows.map((raw: unknown) => {
          const row = asRecord(raw);

          return {
            id: text(row, "id"),
            leadId: text(row, "lead_id"),
            activityType: text(
              row,
              "activity_type"
            ),
            oldValue: text(
              row,
              "old_value"
            ),
            newValue: text(
              row,
              "new_value"
            ),
            summary: text(
              row,
              "summary"
            ),
            createdAt: text(
              row,
              "created_at"
            ),
            businessName:
              text(
                row,
                "business_name"
              ) || "Buyer Deal",
            contactName: text(
              row,
              "name"
            ),
            email: text(
              row,
              "email"
            ),
          } satisfies Activity;
        });

      setActivities(nextActivities);

      setStatus(
        `${nextActivities.length} persistent Deal Desk activities loaded from SQLite.`
      );
    } catch (error) {
      setStatus(
        error instanceof Error
          ? `Activity error: ${error.message}`
          : "Deal activity could not be loaded."
      );
    }
  }, []);

  useEffect(() => {
    const refresh = () => {
      void loadActivity();
    };

    void loadActivity();

    window.addEventListener(
      "wolf-os-pipeline-activity-updated",
      refresh
    );

    return () => {
      window.removeEventListener(
        "wolf-os-pipeline-activity-updated",
        refresh
      );
    };
  }, [loadActivity]);

  return (
    <section className="deal-activity-timeline">
      <header className="deal-activity-header">
        <div>
          <p className="deal-activity-kicker">
            WOLF OS DEAL HISTORY
          </p>

          <h2>Deal Activity Audit Trail</h2>

          <p>
            Timestamped SQLite history for pipeline
            stage movement, value changes, and next
            actions.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadActivity()}
        >
          Refresh Activity
        </button>
      </header>

      <div className="deal-activity-status">
        {status}
      </div>

      {activities.length === 0 ? (
        <div className="deal-activity-empty">
          No deal changes recorded yet. Advance a
          buyer deal or edit its value to create the
          first persistent activity record.
        </div>
      ) : (
        <div className="deal-activity-stack">
          {activities.map((activity) => (
            <article
              className="deal-activity-card"
              key={activity.id}
            >
              <div className="deal-activity-marker" />

              <div className="deal-activity-content">
                <div className="deal-activity-topline">
                  <span>
                    {activityLabel(
                      activity.activityType
                    )}
                  </span>

                  <time>
                    {formatActivityTime(
                      activity.createdAt
                    )}
                  </time>
                </div>

                <h3>
                  {activity.businessName}
                </h3>

                <p>
                  {activity.summary}
                </p>

                {activity.contactName ||
                activity.email ? (
                  <small>
                    {activity.contactName}
                    {activity.email
                      ? ` · ${activity.email}`
                      : ""}
                  </small>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
'''


activity_css_code = r'''.deal-activity-timeline {
  margin-top: 28px;
  padding: 26px;
  border: 1px solid rgba(110, 170, 255, 0.2);
  border-radius: 24px;
  background:
    radial-gradient(circle at 95% 0%, rgba(55, 130, 255, 0.1), transparent 30%),
    linear-gradient(145deg, rgba(8, 11, 17, 0.98), rgba(3, 5, 8, 0.98));
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.44);
}

.deal-activity-timeline * {
  box-sizing: border-box;
}

.deal-activity-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.deal-activity-kicker {
  margin: 0 0 7px;
  color: #87b9ff;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.17em;
  text-transform: uppercase;
}

.deal-activity-header h2 {
  margin: 0;
  color: #fff;
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  letter-spacing: -0.04em;
}

.deal-activity-header p {
  max-width: 720px;
  margin: 9px 0 0;
  color: rgba(234, 241, 249, 0.63);
  line-height: 1.55;
}

.deal-activity-header button {
  flex-shrink: 0;
  padding: 11px 14px;
  border: 1px solid rgba(130, 187, 255, 0.32);
  border-radius: 11px;
  background: rgba(77, 137, 220, 0.1);
  color: #d9e9ff;
  font-size: 0.76rem;
  font-weight: 900;
  cursor: pointer;
}

.deal-activity-status {
  margin: 16px 0;
  padding: 11px 14px;
  border-left: 3px solid #78aef9;
  border-radius: 8px;
  background: rgba(72, 130, 220, 0.07);
  color: rgba(229, 239, 251, 0.7);
  font-size: 0.82rem;
}

.deal-activity-stack {
  display: grid;
  gap: 11px;
}

.deal-activity-card {
  position: relative;
  display: grid;
  grid-template-columns: 14px 1fr;
  gap: 14px;
  padding: 17px;
  border: 1px solid rgba(255, 255, 255, 0.075);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.025);
}

.deal-activity-marker {
  width: 10px;
  height: 10px;
  margin-top: 5px;
  border-radius: 50%;
  background: #83b8ff;
  box-shadow: 0 0 16px rgba(106, 168, 255, 0.65);
}

.deal-activity-content {
  min-width: 0;
}

.deal-activity-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
}

.deal-activity-topline span {
  color: #91c0ff;
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.deal-activity-topline time {
  color: rgba(231, 239, 248, 0.43);
  font-size: 0.7rem;
}

.deal-activity-card h3 {
  margin: 8px 0 0;
  color: #fff;
  font-size: 1rem;
}

.deal-activity-card p {
  margin: 7px 0 0;
  color: rgba(235, 242, 249, 0.69);
  line-height: 1.5;
}

.deal-activity-card small {
  display: block;
  margin-top: 8px;
  color: rgba(226, 235, 245, 0.43);
}

.deal-activity-empty {
  padding: 34px;
  border: 1px dashed rgba(255, 255, 255, 0.13);
  border-radius: 16px;
  color: rgba(233, 240, 247, 0.55);
  text-align: center;
}

@media (max-width: 680px) {
  .deal-activity-timeline {
    padding: 18px;
  }

  .deal-activity-header,
  .deal-activity-topline {
    align-items: flex-start;
    flex-direction: column;
  }

  .deal-activity-header button {
    width: 100%;
  }
}
'''


ACTIVITY_COMPONENT.write_text(
    activity_component_code,
    encoding="utf-8",
)

ACTIVITY_CSS.write_text(
    activity_css_code,
    encoding="utf-8",
)

print(
    "Created DealActivityTimeline component."
)


app_text = APP.read_text(
    encoding="utf-8"
)

import_line = (
    'import DealActivityTimeline '
    'from "./components/DealActivityTimeline";'
)

if import_line not in app_text:
    pipeline_import = (
        'import BuyerPipelineBoard '
        'from "./components/BuyerPipelineBoard";'
    )

    app_text = replace_once(
        app_text,
        pipeline_import,
        pipeline_import
        + "\n"
        + import_line,
        "Deal Activity import",
    )
else:
    print(
        "Deal Activity import already exists."
    )


activity_call = "<DealActivityTimeline />"

if activity_call not in app_text:
    pipeline_call = (
        "<BuyerPipelineBoard "
        "setupRequests={setupRequests} />"
    )

    app_text = replace_once(
        app_text,
        pipeline_call,
        pipeline_call
        + "\n"
        + "      "
        + activity_call,
        "Deal Activity panel placement",
    )
else:
    print(
        "Deal Activity panel already inserted."
    )


APP.write_text(
    app_text,
    encoding="utf-8",
)


print()
print("Checking Flask routes...")

backend_python = (
    BACKEND
    / ".venv"
    / "Scripts"
    / "python.exe"
)

result = subprocess.run(
    [
        str(backend_python),
        "-c",
        (
            "import wsgi; "
            "rules=[str(r) for r in wsgi.app.url_map.iter_rules()]; "
            "assert '/api/owner/pipeline/activity' in rules; "
            "print('FLASK DEAL ACTIVITY ROUTE OK')"
        ),
    ],
    cwd=BACKEND,
    text=True,
)

if result.returncode != 0:
    raise SystemExit(
        "Backend activity route check failed."
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
        "Frontend build failed. Review the error above."
    )


print()
print(
    "SUCCESS: DEAL ACTIVITY AUDIT TRAIL INSTALLED."
)
print(
    "Pipeline changes now create timestamped SQLite activity records."
)
print(
    "Owner Console now includes a persistent Deal Activity Audit Trail."
)
print(
    "Restart WOLF OS before testing."
)