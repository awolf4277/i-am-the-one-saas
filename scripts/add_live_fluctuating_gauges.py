from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil


ROOT = Path(r"X:\i-am-the-one-saas")
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"
CSS_PATH = ROOT / "frontend" / "src" / "styles.css"

BACKUP_ROOT = (
    ROOT
    / "backups"
    / "live-fluctuating-gauges"
    / datetime.now().strftime("%Y%m%d-%H%M%S")
)

APP_MARKER = "WOLF_LIVE_GAUGE_ENGINE_V1"
CSS_MARKER = "WOLF_LIVE_GAUGE_ENGINE_V1"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


for path in (APP_PATH, CSS_PATH):
    if not path.exists():
        fail(f"Missing required file: {path}")

BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
shutil.copy2(APP_PATH, BACKUP_ROOT / "App.tsx")
shutil.copy2(CSS_PATH, BACKUP_ROOT / "styles.css")

app_text = APP_PATH.read_text(encoding="utf-8")
css_text = CSS_PATH.read_text(encoding="utf-8")

if APP_MARKER in app_text:
    print("Live gauge engine is already installed in App.tsx.")
else:
    pattern = re.compile(
        r"^function WolfCockpitPanel\(\{[\s\S]*?^}\r?\n",
        re.MULTILINE,
    )

    matches = list(pattern.finditer(app_text))

    if len(matches) != 1:
        fail(
            "Expected exactly one WolfCockpitPanel function, "
            f"but found {len(matches)}."
        )

    match = matches[0]
    old_component = match.group(0)

    required_anchors = [
        "const launchPercent",
        "cockpit-gauge-grid",
        "featuredProduct",
    ]

    for anchor in required_anchors:
        if anchor not in old_component:
            fail(
                "WolfCockpitPanel did not contain expected anchor: "
                f"{anchor}"
            )

    new_component = r'''// WOLF_LIVE_GAUGE_ENGINE_V1
type LiveCockpitGaugeTone =
  | "launch"
  | "flow"
  | "inventory"
  | "orders";

type LiveCockpitGaugeProps = {
  label: string;
  value: number;
  unit: string;
  status: string;
  detail: string;
  tone: LiveCockpitGaugeTone;
};

function clampGaugeValue(value: number) {
  return Math.max(0, Math.min(100, value));
}

function useFluctuatingGauge(
  target: number,
  volatility: number,
  intervalMs: number
) {
  const safeTarget = clampGaugeValue(target);
  const [value, setValue] = useState(safeTarget);

  useEffect(() => {
    setValue(safeTarget);

    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    if (reduceMotion) {
      return;
    }

    const timer = window.setInterval(() => {
      const jitter =
        (Math.random() - 0.5) * volatility * 2;

      const fluctuatingTarget = clampGaugeValue(
        safeTarget + jitter
      );

      setValue((current) => {
        const eased =
          current +
          (fluctuatingTarget - current) * 0.64;

        return Math.round(eased * 10) / 10;
      });
    }, intervalMs);

    return () => window.clearInterval(timer);
  }, [safeTarget, volatility, intervalMs]);

  return value;
}

function LiveCockpitGauge({
  label,
  value,
  unit,
  status,
  detail,
  tone
}: LiveCockpitGaugeProps) {
  const safeValue = clampGaugeValue(value);
  const needleAngle =
    -132 + (safeValue / 100) * 264;

  const gaugeStyle = {
    "--live-gauge-progress": `${safeValue * 2.64}deg`,
    "--live-gauge-angle": `${needleAngle}deg`
  } as React.CSSProperties;

  return (
    <article
      className={`live-cockpit-gauge live-cockpit-gauge-${tone}`}
    >
      <div
        className="live-cockpit-gauge-face"
        style={gaugeStyle}
        role="img"
        aria-label={`${label}: ${Math.round(safeValue)}${unit}`}
      >
        <div
          className="live-cockpit-gauge-ticks"
          aria-hidden="true"
        />

        <div
          className="live-cockpit-gauge-needle"
          aria-hidden="true"
        >
          <span />
        </div>

        <div
          className="live-cockpit-gauge-hub"
          aria-hidden="true"
        />

        <div className="live-cockpit-gauge-readout">
          <strong>{Math.round(safeValue)}</strong>
          <span>{unit}</span>
        </div>
      </div>

      <div className="live-cockpit-gauge-copy">
        <small>{label}</small>
        <strong>{status}</strong>
        <span>{detail}</span>
      </div>
    </article>
  );
}

function WolfCockpitPanel({
  health,
  productCount,
  storeCount,
  orderCount,
  featuredProduct
}: {
  health: ApiHealth | null;
  productCount: number;
  storeCount: number;
  orderCount: number;
  featuredProduct?: Product;
}) {
  const online = Boolean(health?.ok);

  const launchTarget = online
    ? Math.min(
        98,
        79 +
          Math.min(storeCount, 3) * 5 +
          Math.min(orderCount, 5) * 2
      )
    : 8;

  const buyerFlowTarget = online
    ? Math.min(
        97,
        61 +
          Math.min(productCount, 10) * 3 +
          Math.min(orderCount, 4)
      )
    : 6;

  const inventoryTarget = online
    ? Math.min(
        97,
        53 + Math.min(productCount, 10) * 4
      )
    : 5;

  const orderTarget = online
    ? Math.min(
        98,
        39 + Math.min(orderCount, 7) * 8
      )
    : 4;

  const launchGauge = useFluctuatingGauge(
    launchTarget,
    online ? 2.2 : 0.4,
    760
  );

  const buyerFlowGauge = useFluctuatingGauge(
    buyerFlowTarget,
    online ? 1.8 : 0.35,
    910
  );

  const inventoryGauge = useFluctuatingGauge(
    inventoryTarget,
    online ? 1.3 : 0.3,
    1040
  );

  const orderGauge = useFluctuatingGauge(
    orderTarget,
    online ? 2.8 : 0.5,
    830
  );

  return (
    <section className="wolf-cockpit-panel live-cockpit-panel">
      <div className="cockpit-header">
        <div>
          <p className="cockpit-kicker">
            WOLF OS™ LIVE COCKPIT
          </p>

          <h2>
            Real data targets with continuously moving gauges.
          </h2>

          <p>
            API health, stores, products, and orders determine
            each gauge target. Subtle engine-style movement keeps
            the cockpit alive without inventing business data.
          </p>
        </div>

        <div className="cockpit-status-stack">
          <span>
            ENGINE: {online ? "ONLINE" : "CHECK"}
          </span>

          <span>
            GAUGES: {online ? "LIVE MOTION" : "IDLE"}
          </span>

          <span>
            MODE: DATA DRIVEN
          </span>
        </div>
      </div>

      <div className="live-cockpit-gauge-grid">
        <LiveCockpitGauge
          label="LAUNCH RPM"
          value={launchGauge}
          unit="%"
          status={online ? "ENGINE LIVE" : "ENGINE CHECK"}
          detail={`${storeCount} live ${
            storeCount === 1 ? "store" : "stores"
          } · API ${online ? "online" : "offline"}`}
          tone="launch"
        />

        <LiveCockpitGauge
          label="BUYER FLOW"
          value={buyerFlowGauge}
          unit="%"
          status={
            productCount > 0
              ? "BUYING PATH READY"
              : "LOAD PRODUCTS"
          }
          detail={`${productCount} live ${
            productCount === 1 ? "product" : "products"
          } powering the storefront`}
          tone="flow"
        />

        <LiveCockpitGauge
          label="INVENTORY LOAD"
          value={inventoryGauge}
          unit="%"
          status={
            productCount > 0
              ? "CATALOG ACTIVE"
              : "CATALOG EMPTY"
          }
          detail={`${productCount} inventory ${
            productCount === 1 ? "record" : "records"
          } connected`}
          tone="inventory"
        />

        <LiveCockpitGauge
          label="ORDER PULSE"
          value={orderGauge}
          unit="%"
          status={
            orderCount > 0
              ? "REVENUE SIGNAL"
              : "AWAITING ORDER"
          }
          detail={`${orderCount} real ${
            orderCount === 1 ? "order" : "orders"
          } recorded`}
          tone="orders"
        />
      </div>

      <div className="live-cockpit-signal-strip">
        <div>
          <small>FEATURED SIGNAL</small>
          <strong>
            {featuredProduct?.name ||
              "Wolf Signature Hoodie"}
          </strong>
        </div>

        <div>
          <small>LIVE PRICE</small>
          <strong>
            {money(featuredProduct?.price_cents || 9900)}
          </strong>
        </div>

        <div>
          <small>SYSTEM STATE</small>
          <strong>
            {online ? "READY TO SELL" : "API CHECK"}
          </strong>
        </div>

        <div className="live-cockpit-motion-indicator">
          <span aria-hidden="true" />
          <small>
            {online
              ? "GAUGE TELEMETRY ACTIVE"
              : "GAUGES IN SAFE IDLE"}
          </small>
        </div>
      </div>
    </section>
  );
}
'''

    app_text = (
        app_text[:match.start()]
        + new_component
        + app_text[match.end():]
    )

    APP_PATH.write_text(
        app_text,
        encoding="utf-8",
        newline="\n",
    )

    print("Replaced static WolfCockpitPanel.")

if CSS_MARKER in css_text:
    print("Live gauge CSS is already installed.")
else:
    live_gauge_css = r'''

/* WOLF_LIVE_GAUGE_ENGINE_V1 */
.live-cockpit-panel {
  isolation: isolate;
}

.live-cockpit-gauge-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-top: 26px;
}

.live-cockpit-gauge {
  position: relative;
  min-width: 0;
  padding: 18px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 24px;
  background:
    radial-gradient(
      circle at 50% 18%,
      rgba(125, 255, 189, 0.08),
      transparent 48%
    ),
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.075),
      rgba(255, 255, 255, 0.025)
    ),
    rgba(0, 0, 0, 0.38);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 20px 48px rgba(0, 0, 0, 0.28);
}

.live-cockpit-gauge::after {
  content: "";
  position: absolute;
  width: 70%;
  height: 42%;
  left: 15%;
  bottom: -28%;
  border-radius: 50%;
  background: rgba(125, 255, 189, 0.14);
  filter: blur(30px);
  pointer-events: none;
}

.live-cockpit-gauge-face {
  --live-gauge-progress: 0deg;
  --live-gauge-angle: -132deg;

  position: relative;
  width: min(100%, 190px);
  aspect-ratio: 1;
  margin: 0 auto 16px;
  border-radius: 50%;
  background:
    radial-gradient(
      circle at center,
      rgba(5, 9, 13, 0.98) 0 57%,
      transparent 58%
    ),
    conic-gradient(
      from 228deg,
      rgba(125, 255, 189, 0.98)
        0deg var(--live-gauge-progress),
      rgba(255, 255, 255, 0.09)
        var(--live-gauge-progress) 264deg,
      transparent 264deg 360deg
    );
  box-shadow:
    inset 0 0 34px rgba(0, 0, 0, 0.84),
    0 0 34px rgba(125, 255, 189, 0.08);
}

.live-cockpit-gauge-face::before {
  content: "";
  position: absolute;
  inset: 8%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  background:
    radial-gradient(
      circle at 50% 34%,
      rgba(255, 255, 255, 0.09),
      transparent 35%
    ),
    rgba(2, 5, 8, 0.94);
  box-shadow:
    inset 0 0 35px rgba(0, 0, 0, 0.9),
    inset 0 0 12px rgba(125, 255, 189, 0.05);
}

.live-cockpit-gauge-ticks {
  position: absolute;
  inset: 7%;
  z-index: 1;
  border-radius: 50%;
  background:
    repeating-conic-gradient(
      from 228deg,
      rgba(255, 255, 255, 0.7) 0deg 1deg,
      transparent 1deg 11deg
    );
  -webkit-mask:
    radial-gradient(
      circle,
      transparent 0 68%,
      #000 69% 74%,
      transparent 75%
    );
  mask:
    radial-gradient(
      circle,
      transparent 0 68%,
      #000 69% 74%,
      transparent 75%
    );
  opacity: 0.62;
}

.live-cockpit-gauge-needle {
  position: absolute;
  z-index: 4;
  left: 50%;
  top: 50%;
  width: 39%;
  height: 4px;
  transform-origin: 0 50%;
  transform:
    translateY(-50%)
    rotate(var(--live-gauge-angle));
  transition:
    transform 720ms cubic-bezier(0.22, 1, 0.36, 1);
}

.live-cockpit-gauge-needle span {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 999px;
  background:
    linear-gradient(
      90deg,
      rgba(255, 255, 255, 0.96),
      rgba(125, 255, 189, 0.96)
    );
  box-shadow:
    0 0 12px rgba(125, 255, 189, 0.55);
  clip-path: polygon(0 22%, 100% 50%, 0 78%);
}

.live-cockpit-gauge-hub {
  position: absolute;
  z-index: 5;
  left: 50%;
  top: 50%;
  width: 18px;
  height: 18px;
  transform: translate(-50%, -50%);
  border: 3px solid rgba(255, 255, 255, 0.68);
  border-radius: 50%;
  background: rgba(5, 8, 12, 1);
  box-shadow:
    0 0 0 5px rgba(125, 255, 189, 0.08),
    0 0 16px rgba(125, 255, 189, 0.36);
}

.live-cockpit-gauge-readout {
  position: absolute;
  z-index: 3;
  left: 50%;
  bottom: 17%;
  display: flex;
  align-items: baseline;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.96);
}

.live-cockpit-gauge-readout strong {
  font-size: clamp(1.45rem, 3vw, 2.05rem);
  font-weight: 950;
  letter-spacing: -0.06em;
}

.live-cockpit-gauge-readout span {
  margin-left: 3px;
  color: rgba(125, 255, 189, 0.82);
  font-size: 0.72rem;
  font-weight: 900;
}

.live-cockpit-gauge-copy {
  position: relative;
  z-index: 2;
  display: grid;
  gap: 5px;
  text-align: center;
}

.live-cockpit-gauge-copy small {
  color: rgba(125, 255, 189, 0.82);
  font-size: 0.7rem;
  font-weight: 950;
  letter-spacing: 0.15em;
}

.live-cockpit-gauge-copy strong {
  color: rgba(255, 255, 255, 0.95);
  font-size: 0.9rem;
  font-weight: 950;
}

.live-cockpit-gauge-copy span {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.76rem;
  line-height: 1.45;
}

.live-cockpit-gauge-flow
  .live-cockpit-gauge-face {
  filter: hue-rotate(10deg);
}

.live-cockpit-gauge-inventory
  .live-cockpit-gauge-face {
  filter: hue-rotate(-12deg);
}

.live-cockpit-gauge-orders
  .live-cockpit-gauge-face {
  filter: hue-rotate(25deg);
}

.live-cockpit-signal-strip {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns:
    minmax(0, 1.4fr)
    repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.live-cockpit-signal-strip > div {
  min-width: 0;
  padding: 11px 13px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 15px;
  background: rgba(0, 0, 0, 0.28);
}

.live-cockpit-signal-strip small {
  display: block;
  margin-bottom: 4px;
  color: rgba(255, 255, 255, 0.52);
  font-size: 0.66rem;
  font-weight: 900;
  letter-spacing: 0.1em;
}

.live-cockpit-signal-strip strong {
  display: block;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.94);
  font-size: 0.86rem;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.live-cockpit-motion-indicator {
  display: flex;
  align-items: center;
  gap: 9px;
}

.live-cockpit-motion-indicator span {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: rgba(125, 255, 189, 0.95);
  box-shadow:
    0 0 18px rgba(125, 255, 189, 0.62);
  animation:
    live-cockpit-telemetry-pulse 1.15s ease-in-out infinite;
}

.live-cockpit-motion-indicator small {
  margin: 0;
}

@keyframes live-cockpit-telemetry-pulse {
  0%,
  100% {
    opacity: 0.48;
    transform: scale(0.82);
  }

  50% {
    opacity: 1;
    transform: scale(1.12);
  }
}

@media (max-width: 980px) {
  .live-cockpit-gauge-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .live-cockpit-signal-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .live-cockpit-gauge-grid,
  .live-cockpit-signal-strip {
    grid-template-columns: 1fr;
  }

  .live-cockpit-gauge {
    padding: 16px;
  }

  .live-cockpit-gauge-face {
    width: min(76vw, 205px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .live-cockpit-gauge-needle {
    transition: none;
  }

  .live-cockpit-motion-indicator span {
    animation: none;
  }
}
'''

    if css_text and not css_text.endswith("\n"):
        css_text += "\n"

    css_text += live_gauge_css

    CSS_PATH.write_text(
        css_text,
        encoding="utf-8",
        newline="\n",
    )

    print("Added live fluctuating gauge CSS.")

print(f"Backups created in: {BACKUP_ROOT}")
print(f"Updated: {APP_PATH}")
print(f"Updated: {CSS_PATH}")
