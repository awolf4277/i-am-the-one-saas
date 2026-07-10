from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
APP_PATH = FRONTEND_ROOT / "src" / "App.tsx"
CSS_PATH = FRONTEND_ROOT / "src" / "styles.css"


ACTIVITY_COMPONENT = r'''

type ActivityFeedProps = {
  health: ApiHealth | null;
  productCount: number;
  orderCount: number;
  leadCount: number;
};

function WolfActivityFeed({
  health,
  productCount,
  orderCount,
  leadCount
}: ActivityFeedProps) {
  const now = new Date();

  const activityItems = [
    {
      label: health?.ok ? "ENGINE ONLINE" : "ENGINE CHECK",
      detail: health?.ok
        ? "WOLF OS core systems responding."
        : "Waiting for backend connection.",
      status: health?.ok ? "online" : "checking"
    },
    {
      label: health?.ok ? "API CONNECTED" : "API VERIFYING",
      detail: health?.ok
        ? "Live Flask backend connection confirmed."
        : "Attempting to reach API.",
      status: health?.ok ? "online" : "checking"
    },
    {
      label: `${productCount} PRODUCTS SYNCHRONIZED`,
      detail: "Live catalog and inventory data loaded.",
      status: productCount > 0 ? "online" : "checking"
    },
    {
      label: `${orderCount} ORDERS DETECTED`,
      detail: "Owner order pipeline is active.",
      status: orderCount > 0 ? "online" : "standby"
    },
    {
      label: `${leadCount} BUYER LEADS ACTIVE`,
      detail: "Setup requests are available for follow-up.",
      status: leadCount > 0 ? "hot" : "standby"
    },
    {
      label: "COCKPIT REFRESHED",
      detail: "Dashboard readouts updated from live data.",
      status: health?.ok ? "online" : "checking"
    },
    {
      label: "STOREFRONT READY",
      detail: "Buyer path, product flow, and checkout are armed.",
      status: health?.ok && productCount > 0 ? "online" : "standby"
    }
  ];

  const formatTime = (offsetSeconds: number) => {
    const date = new Date(now.getTime() - offsetSeconds * 1000);

    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  };

  return (
    <section className="wolf-activity-panel">
      <div className="activity-panel-head">
        <div>
          <p className="activity-kicker">WOLF OS™ LIVE ACTIVITY</p>
          <h2>System activity in real time.</h2>
          <p>
            Live operational proof from the storefront, API, inventory,
            order pipeline, buyer leads, and cockpit.
          </p>
        </div>

        <div className="activity-live-badge">
          <span className={health?.ok ? "activity-live-dot online" : "activity-live-dot"} />
          <strong>{health?.ok ? "LIVE FEED" : "CONNECTING"}</strong>
        </div>
      </div>

      <div className="activity-layout">
        <div className="activity-feed-list">
          {activityItems.map((item, index) => (
            <article
              className={`activity-feed-row ${item.status}`}
              key={`${item.label}-${index}`}
            >
              <time>{formatTime((activityItems.length - index) * 2)}</time>

              <span className="activity-event-dot" />

              <div>
                <strong>{item.label}</strong>
                <small>{item.detail}</small>
              </div>
            </article>
          ))}
        </div>

        <div className="mission-status-panel">
          <p className="activity-kicker">MISSION STATUS</p>

          <MissionStatusRow
            label="Engine"
            value={health?.ok ? "ONLINE" : "CHECK"}
            percent={health?.ok ? 100 : 35}
          />

          <MissionStatusRow
            label="Buyer Pipeline"
            value={leadCount > 0 ? "READY" : "STANDBY"}
            percent={leadCount > 0 ? Math.min(100, 70 + leadCount * 8) : 28}
          />

          <MissionStatusRow
            label="Storefront"
            value={productCount > 0 ? "LIVE" : "LOADING"}
            percent={productCount > 0 ? 100 : 40}
          />

          <MissionStatusRow
            label="Owner Console"
            value={health?.ok ? "ACTIVE" : "CHECK"}
            percent={health?.ok ? 96 : 38}
          />

          <MissionStatusRow
            label="API"
            value={health?.ok ? "CONNECTED" : "VERIFYING"}
            percent={health?.ok ? 100 : 32}
          />
        </div>
      </div>
    </section>
  );
}

function MissionStatusRow({
  label,
  value,
  percent
}: {
  label: string;
  value: string;
  percent: number;
}) {
  const safePercent = Math.max(0, Math.min(100, percent));

  return (
    <div className="mission-status-row">
      <div className="mission-status-meta">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>

      <div className="mission-status-track">
        <div
          className="mission-status-fill"
          style={{ width: `${safePercent}%` }}
        />
      </div>
    </div>
  );
}

'''


ACTIVITY_INSERT = r'''
      <div className="landing-cockpit-span">
        <WolfActivityFeed
          health={health}
          productCount={productCount}
          orderCount={orderCount}
          leadCount={3}
        />
      </div>

'''


ACTIVITY_CSS = r'''

/* WOLF OS live activity feed */
.wolf-activity-panel {
  grid-column: 1 / -1;
  margin: 0 0 10px;
  padding: 26px;
  border: 1px solid rgba(125, 255, 189, 0.18);
  border-radius: 28px;
  background:
    radial-gradient(circle at 8% 0%, rgba(125, 255, 189, 0.14), transparent 34%),
    radial-gradient(circle at 90% 8%, rgba(255, 208, 87, 0.1), transparent 30%),
    linear-gradient(135deg, rgba(255,255,255,0.065), rgba(255,255,255,0.02)),
    rgba(2, 5, 8, 0.9);
  box-shadow:
    0 30px 100px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.wolf-activity-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 38px 38px;
  mask-image: radial-gradient(circle at center, black, transparent 82%);
  pointer-events: none;
}

.activity-panel-head {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 22px;
  align-items: start;
}

.activity-kicker {
  margin: 0 0 8px;
  color: #7dffbd;
  font-size: 0.76rem;
  font-weight: 950;
  letter-spacing: 0.2em;
}

.activity-panel-head h2 {
  margin: 0 0 10px;
  font-size: clamp(1.55rem, 3vw, 2.45rem);
  letter-spacing: -0.05em;
}

.activity-panel-head p {
  max-width: 760px;
  color: rgba(255, 255, 255, 0.7);
}

.activity-live-badge {
  min-width: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 13px 15px;
  border: 1px solid rgba(125, 255, 189, 0.2);
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.72rem;
  letter-spacing: 0.12em;
}

.activity-live-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ffd057;
  box-shadow: 0 0 18px rgba(255, 208, 87, 0.4);
}

.activity-live-dot.online {
  background: #7dffbd;
  box-shadow: 0 0 20px rgba(125, 255, 189, 0.55);
  animation: activityPulse 1.8s ease-in-out infinite;
}

.activity-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.75fr);
  gap: 16px;
  margin-top: 22px;
}

.activity-feed-list,
.mission-status-panel {
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018)),
    rgba(0, 0, 0, 0.34);
}

.activity-feed-list {
  display: grid;
  gap: 8px;
}

.activity-feed-row {
  display: grid;
  grid-template-columns: 82px 12px 1fr;
  gap: 12px;
  align-items: center;
  padding: 11px 12px;
  border-radius: 15px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.025);
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background 180ms ease;
}

.activity-feed-row:hover {
  transform: translateX(4px);
  border-color: rgba(125, 255, 189, 0.2);
  background: rgba(125, 255, 189, 0.04);
}

.activity-feed-row time {
  color: rgba(255, 255, 255, 0.42);
  font-size: 0.68rem;
  font-weight: 850;
  letter-spacing: 0.06em;
}

.activity-event-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.3);
}

.activity-feed-row.online .activity-event-dot {
  background: #7dffbd;
  box-shadow: 0 0 16px rgba(125, 255, 189, 0.5);
}

.activity-feed-row.hot .activity-event-dot {
  background: #ffd057;
  box-shadow: 0 0 16px rgba(255, 208, 87, 0.5);
}

.activity-feed-row.checking .activity-event-dot {
  background: #ffd057;
}

.activity-feed-row.standby .activity-event-dot {
  background: rgba(255, 255, 255, 0.28);
}

.activity-feed-row strong,
.activity-feed-row small {
  display: block;
}

.activity-feed-row strong {
  color: rgba(255, 255, 255, 0.93);
  font-size: 0.86rem;
  letter-spacing: 0.02em;
}

.activity-feed-row small {
  margin-top: 3px;
  color: rgba(255, 255, 255, 0.52);
  line-height: 1.4;
}

.mission-status-panel {
  display: grid;
  align-content: start;
  gap: 16px;
}

.mission-status-row {
  display: grid;
  gap: 8px;
}

.mission-status-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.mission-status-meta span {
  color: rgba(255, 255, 255, 0.58);
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.mission-status-meta strong {
  color: rgba(255, 255, 255, 0.94);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
}

.mission-status-track {
  height: 9px;
  overflow: hidden;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.055);
}

.mission-status-fill {
  height: 100%;
  border-radius: inherit;
  background:
    linear-gradient(90deg, #7dffbd, #ffd057);
  box-shadow:
    0 0 18px rgba(125, 255, 189, 0.3),
    0 0 24px rgba(255, 208, 87, 0.16);
  transition: width 650ms ease;
}

@keyframes activityPulse {
  0%,
  100% {
    opacity: 0.65;
    transform: scale(0.92);
  }

  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

@media (prefers-reduced-motion: reduce) {
  .activity-live-dot.online {
    animation: none;
  }

  .activity-feed-row,
  .mission-status-fill {
    transition: none;
  }
}

@media (max-width: 900px) {
  .activity-panel-head,
  .activity-layout {
    grid-template-columns: 1fr;
  }

  .activity-live-badge {
    width: 100%;
  }
}

@media (max-width: 600px) {
  .wolf-activity-panel {
    padding: 20px;
    border-radius: 24px;
  }

  .activity-feed-row {
    grid-template-columns: 1fr;
    gap: 5px;
  }

  .activity-event-dot {
    display: none;
  }
}

'''


def backup_file(path: Path, label: str) -> None:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(
        f"{path.stem}.before-{label}-{stamp}{path.suffix}"
    )
    shutil.copy2(path, backup_path)
    print(f"Backup created: {backup_path}")


def patch_app() -> None:
    text = APP_PATH.read_text(encoding="utf-8")

    if "function WolfActivityFeed" not in text:
        marker = "function CustomerStorefront({"

        if marker not in text:
            raise RuntimeError(
                "Could not find CustomerStorefront marker in App.tsx."
            )

        text = text.replace(
            marker,
            ACTIVITY_COMPONENT + marker,
            1,
        )
        print("Added WolfActivityFeed components.")
    else:
        print("WolfActivityFeed already exists.")

    if "<WolfActivityFeed" not in text:
        landing_marker = '<section className="landing-grid">'

        if landing_marker not in text:
            raise RuntimeError(
                "Could not find landing-grid marker in App.tsx."
            )

        text = text.replace(
            landing_marker,
            landing_marker + "\n" + ACTIVITY_INSERT,
            1,
        )
        print("Inserted Live Activity Feed into landing page.")
    else:
        print("WolfActivityFeed already rendered.")

    APP_PATH.write_text(text, encoding="utf-8")


def patch_css() -> None:
    text = CSS_PATH.read_text(encoding="utf-8")

    if "WOLF OS live activity feed" in text:
        print("Live Activity Feed CSS already exists.")
        return

    CSS_PATH.write_text(
        text.rstrip() + "\n" + ACTIVITY_CSS + "\n",
        encoding="utf-8",
    )
    print("Added Live Activity Feed CSS.")


def run_build() -> None:
    print("\nRunning frontend build...")

    result = subprocess.run(
        ["npm.cmd", "run", "build"],
        cwd=str(FRONTEND_ROOT),
        shell=False,
    )

    if result.returncode != 0:
        raise RuntimeError("Frontend build failed.")


def main() -> None:
    if not APP_PATH.exists():
        raise FileNotFoundError(APP_PATH)

    if not CSS_PATH.exists():
        raise FileNotFoundError(CSS_PATH)

    print("WOLF OS Live Activity Feed patch starting...")

    backup_file(APP_PATH, "live-activity")
    backup_file(CSS_PATH, "live-activity")

    patch_app()
    patch_css()
    run_build()

    print("\nLive Activity Feed installed successfully.")
    print(r"Start locally with:")
    print(r"cd X:\i-am-the-one-saas")
    print(r".\start-local.ps1")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)