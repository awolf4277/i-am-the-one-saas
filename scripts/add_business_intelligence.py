from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
APP_PATH = FRONTEND_ROOT / "src" / "App.tsx"
CSS_PATH = FRONTEND_ROOT / "src" / "styles.css"


BI_COMPONENT = r'''

type BusinessIntelligenceProps = {
  health: ApiHealth | null;
  products: Product[];
  orders: Order[];
  setupRequests: SetupRequest[];
  analytics: AnalyticsSummary | null;
};

function BusinessIntelligencePanel({
  health,
  products,
  orders,
  setupRequests,
  analytics
}: BusinessIntelligenceProps) {
  const inventoryValue = products.reduce((sum, product) => {
    return sum + Number(product.price_cents || 0) * Number(product.stock || 0);
  }, 0);

  const totalRevenue = orders.reduce((sum, order) => {
    return sum + Number(order.total_cents || 0);
  }, 0);

  const averageOrder = orders.length
    ? Math.round(totalRevenue / orders.length)
    : 0;

  const lowStockCount = products.filter((product) => {
    return Number(product.stock || 0) <= 3;
  }).length;

  const totalVisits = Number(analytics?.total_visits || 0);
  const visitsToday = Number(analytics?.visits_today || 0);

  const leadRate = totalVisits > 0
    ? Math.round((setupRequests.length / totalVisits) * 100)
    : Number(analytics?.conversion_rate || 0);

  const storeHealth = Math.max(
    0,
    Math.min(
      100,
      50 +
        (health?.ok ? 20 : 0) +
        Math.min(products.length * 2, 15) +
        Math.min(orders.length * 2, 10) +
        Math.min(setupRequests.length, 5) -
        lowStockCount * 2
    )
  );

  const topProduct = [...products]
    .sort((a, b) => {
      return Number(b.price_cents || 0) - Number(a.price_cents || 0);
    })[0];

  const systemValue = inventoryValue + totalRevenue;

  return (
    <section className="business-intelligence-panel">
      <div className="bi-panel-head">
        <div>
          <p className="bi-kicker">WOLF OS™ BUSINESS INTELLIGENCE</p>
          <h2>Operational numbers that make the system feel real.</h2>
          <p>
            Revenue, inventory, buyer activity, store health, and performance
            indicators generated from the current live system data.
          </p>
        </div>

        <div className="bi-health-score">
          <span>STORE HEALTH</span>
          <strong>{storeHealth}%</strong>
          <small>{health?.ok ? "Operational" : "Connection check"}</small>
        </div>
      </div>

      <div className="bi-metric-grid">
        <BiMetric
          label="System Value"
          value={money(systemValue)}
          detail="Inventory value plus captured order value."
          status="green"
        />

        <BiMetric
          label="Captured Revenue"
          value={money(totalRevenue)}
          detail={`${orders.length} orders currently detected.`}
          status="gold"
        />

        <BiMetric
          label="Average Order"
          value={money(averageOrder)}
          detail="Average value across current orders."
          status="green"
        />

        <BiMetric
          label="Inventory Value"
          value={money(inventoryValue)}
          detail={`${products.length} products in the live catalog.`}
          status="blue"
        />

        <BiMetric
          label="Buyer Conversion"
          value={`${leadRate}%`}
          detail={`${setupRequests.length} live buyer leads captured.`}
          status={leadRate > 0 ? "gold" : "muted"}
        />

        <BiMetric
          label="Visits Today"
          value={visitsToday}
          detail={`${totalVisits} total tracked visits.`}
          status="blue"
        />

        <BiMetric
          label="Low Stock"
          value={lowStockCount}
          detail={
            lowStockCount > 0
              ? "Products need owner attention."
              : "Inventory levels are healthy."
          }
          status={lowStockCount > 0 ? "red" : "green"}
        />

        <BiMetric
          label="API Status"
          value={health?.ok ? "LIVE" : "CHECK"}
          detail={health?.version || "WOLF OS backend status."}
          status={health?.ok ? "green" : "red"}
        />
      </div>

      <div className="bi-summary-grid">
        <article className="bi-summary-card">
          <p className="bi-kicker">TOP PRODUCT SIGNAL</p>
          <h3>{topProduct?.name || "No product loaded"}</h3>

          <div className="bi-summary-rows">
            <span>Price</span>
            <strong>{money(topProduct?.price_cents)}</strong>

            <span>Stock</span>
            <strong>{Number(topProduct?.stock || 0)}</strong>

            <span>Category</span>
            <strong>{topProduct?.category || "Premium"}</strong>
          </div>
        </article>

        <article className="bi-summary-card">
          <p className="bi-kicker">PIPELINE SIGNAL</p>
          <h3>
            {setupRequests.length > 0
              ? `${setupRequests.length} buyer leads active`
              : "Waiting for buyer activity"}
          </h3>

          <div className="bi-summary-rows">
            <span>Orders</span>
            <strong>{orders.length}</strong>

            <span>Leads</span>
            <strong>{setupRequests.length}</strong>

            <span>Lead Rate</span>
            <strong>{leadRate}%</strong>
          </div>
        </article>

        <article className="bi-summary-card">
          <p className="bi-kicker">SYSTEM READINESS</p>
          <h3>{storeHealth >= 90 ? "Launch-ready" : "Operational"}</h3>

          <div className="bi-readiness-bars">
            <BiReadiness label="API" percent={health?.ok ? 100 : 35} />
            <BiReadiness
              label="Catalog"
              percent={Math.min(100, 55 + products.length * 5)}
            />
            <BiReadiness
              label="Orders"
              percent={Math.min(100, 50 + orders.length * 8)}
            />
            <BiReadiness
              label="Leads"
              percent={Math.min(100, 55 + setupRequests.length * 10)}
            />
          </div>
        </article>
      </div>
    </section>
  );
}

function BiMetric({
  label,
  value,
  detail,
  status
}: {
  label: string;
  value: React.ReactNode;
  detail: string;
  status: "green" | "gold" | "blue" | "red" | "muted";
}) {
  return (
    <article className={`bi-metric-card ${status}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function BiReadiness({
  label,
  percent
}: {
  label: string;
  percent: number;
}) {
  const safePercent = Math.max(0, Math.min(100, percent));

  return (
    <div className="bi-readiness-row">
      <div>
        <span>{label}</span>
        <strong>{safePercent}%</strong>
      </div>

      <div className="bi-readiness-track">
        <div
          className="bi-readiness-fill"
          style={{ width: `${safePercent}%` }}
        />
      </div>
    </div>
  );
}

'''


OWNER_INSERT = r'''
      <BusinessIntelligencePanel
        health={health}
        products={products}
        orders={orders}
        setupRequests={setupRequests}
        analytics={analytics}
      />

'''


BI_CSS = r'''

/* WOLF OS Business Intelligence */
.business-intelligence-panel {
  margin: 26px 0;
  padding: 28px;
  border: 1px solid rgba(125, 255, 189, 0.18);
  border-radius: 30px;
  background:
    radial-gradient(circle at 10% 0%, rgba(125, 255, 189, 0.15), transparent 34%),
    radial-gradient(circle at 90% 8%, rgba(255, 208, 87, 0.11), transparent 30%),
    linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02)),
    rgba(2, 5, 8, 0.92);
  box-shadow:
    0 32px 110px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.business-intelligence-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(circle at center, black, transparent 82%);
  pointer-events: none;
}

.bi-panel-head {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 22px;
  align-items: start;
}

.bi-kicker {
  margin: 0 0 8px;
  color: #7dffbd;
  font-size: 0.76rem;
  font-weight: 950;
  letter-spacing: 0.2em;
}

.bi-panel-head h2 {
  margin: 0 0 10px;
  font-size: clamp(1.6rem, 3vw, 2.55rem);
  letter-spacing: -0.055em;
}

.bi-panel-head p {
  max-width: 800px;
  color: rgba(255, 255, 255, 0.7);
}

.bi-health-score {
  min-width: 180px;
  padding: 18px;
  border: 1px solid rgba(125, 255, 189, 0.22);
  border-radius: 24px;
  background:
    radial-gradient(circle at top, rgba(125, 255, 189, 0.12), transparent 62%),
    rgba(0, 0, 0, 0.4);
  text-align: center;
}

.bi-health-score span,
.bi-health-score small {
  display: block;
  color: rgba(255, 255, 255, 0.52);
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.bi-health-score strong {
  display: block;
  margin: 7px 0;
  color: #7dffbd;
  font-size: clamp(2.6rem, 6vw, 4.2rem);
  line-height: 0.9;
  letter-spacing: -0.09em;
  text-shadow: 0 0 26px rgba(125, 255, 189, 0.34);
}

.bi-metric-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 24px;
}

.bi-metric-card {
  min-height: 150px;
  padding: 17px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 21px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.065), rgba(255,255,255,0.02)),
    rgba(0,0,0,0.34);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.08),
    0 18px 46px rgba(0,0,0,0.26);
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.bi-metric-card:hover {
  transform: translateY(-4px);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.1),
    0 24px 58px rgba(0,0,0,0.32);
}

.bi-metric-card > span,
.bi-metric-card > strong,
.bi-metric-card > small {
  display: block;
}

.bi-metric-card > span {
  color: rgba(255,255,255,0.52);
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.bi-metric-card > strong {
  margin: 13px 0 10px;
  color: rgba(255,255,255,0.96);
  font-size: clamp(1.55rem, 3vw, 2.4rem);
  line-height: 0.95;
  letter-spacing: -0.07em;
}

.bi-metric-card > small {
  color: rgba(255,255,255,0.52);
  line-height: 1.45;
}

.bi-metric-card.green {
  border-color: rgba(125, 255, 189, 0.2);
}

.bi-metric-card.green > strong {
  color: #7dffbd;
}

.bi-metric-card.gold {
  border-color: rgba(255, 208, 87, 0.2);
}

.bi-metric-card.gold > strong {
  color: #ffd057;
}

.bi-metric-card.blue {
  border-color: rgba(100, 190, 255, 0.22);
}

.bi-metric-card.blue > strong {
  color: #91d3ff;
}

.bi-metric-card.red {
  border-color: rgba(255, 92, 92, 0.24);
}

.bi-metric-card.red > strong {
  color: #ff7b7b;
}

.bi-metric-card.muted > strong {
  color: rgba(255,255,255,0.74);
}

.bi-summary-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.bi-summary-card {
  padding: 20px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018)),
    rgba(0,0,0,0.34);
}

.bi-summary-card h3 {
  margin: 0 0 18px;
  font-size: 1.25rem;
  letter-spacing: -0.04em;
}

.bi-summary-rows {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 11px 16px;
}

.bi-summary-rows span {
  color: rgba(255,255,255,0.52);
}

.bi-summary-rows strong {
  color: rgba(255,255,255,0.92);
  text-align: right;
}

.bi-readiness-bars {
  display: grid;
  gap: 13px;
}

.bi-readiness-row {
  display: grid;
  gap: 7px;
}

.bi-readiness-row > div:first-child {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.bi-readiness-row span {
  color: rgba(255,255,255,0.54);
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.bi-readiness-row strong {
  color: rgba(255,255,255,0.9);
  font-size: 0.72rem;
}

.bi-readiness-track {
  height: 9px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 999px;
  background: rgba(255,255,255,0.055);
}

.bi-readiness-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #7dffbd, #ffd057);
  box-shadow:
    0 0 18px rgba(125,255,189,0.3),
    0 0 24px rgba(255,208,87,0.14);
  transition: width 700ms ease;
}

@media (max-width: 1100px) {
  .bi-metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .bi-summary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .business-intelligence-panel {
    padding: 20px;
    border-radius: 24px;
  }

  .bi-panel-head {
    grid-template-columns: 1fr;
  }

  .bi-health-score {
    width: 100%;
  }
}

@media (max-width: 560px) {
  .bi-metric-grid {
    grid-template-columns: 1fr;
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

    if "function BusinessIntelligencePanel" not in text:
        marker = "function CustomerStorefront({"

        if marker not in text:
            raise RuntimeError(
                "Could not find CustomerStorefront marker."
            )

        text = text.replace(
            marker,
            BI_COMPONENT + marker,
            1,
        )

        print("Added Business Intelligence components.")
    else:
        print("Business Intelligence component already exists.")

    if "<BusinessIntelligencePanel" not in text:
        marker = '<div className="metric-grid">'

        owner_start = text.find("function OwnerConsole(")

        if owner_start == -1:
            raise RuntimeError(
                "Could not find OwnerConsole function."
            )

        metric_position = text.find(marker, owner_start)

        if metric_position == -1:
            raise RuntimeError(
                "Could not find owner metric-grid marker."
            )

        text = (
            text[:metric_position]
            + OWNER_INSERT
            + text[metric_position:]
        )

        print("Inserted Business Intelligence panel into Owner Console.")
    else:
        print("Business Intelligence panel already rendered.")

    APP_PATH.write_text(text, encoding="utf-8")


def patch_css() -> None:
    text = CSS_PATH.read_text(encoding="utf-8")

    if "WOLF OS Business Intelligence" in text:
        print("Business Intelligence CSS already exists.")
        return

    CSS_PATH.write_text(
        text.rstrip() + "\n" + BI_CSS + "\n",
        encoding="utf-8",
    )

    print("Added Business Intelligence CSS.")


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

    print("WOLF OS Business Intelligence patch starting...")

    backup_file(APP_PATH, "business-intelligence")
    backup_file(CSS_PATH, "business-intelligence")

    patch_app()
    patch_css()
    run_build()

    print("\nBusiness Intelligence installed successfully.")
    print(r"Start locally with:")
    print(r"cd X:\i-am-the-one-saas")
    print(r".\start-local.ps1")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)
