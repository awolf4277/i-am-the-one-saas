import { useCallback, useEffect, useState } from "react";
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
        `${API_BASE}/api/owner/pipeline-activity?limit=40`,
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
