from pathlib import Path
from datetime import datetime
import shutil
import subprocess

ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND = ROOT / "frontend"

APP = FRONTEND / "src" / "App.tsx"

REVENUE = (
    FRONTEND
    / "src"
    / "components"
    / "RevenueCommandCenter.tsx"
)

STAMP = datetime.now().strftime(
    "%Y%m%d-%H%M%S"
)

BACKUP_DIR = (
    ROOT
    / "backups"
    / "revenue-truth"
)

BACKUP_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def stop(message: str) -> None:
    raise SystemExit(
        f"PATCH STOPPED: {message}"
    )


def replace_once(
    text: str,
    old: str,
    new: str,
    label: str,
) -> str:
    count = text.count(old)

    if count != 1:
        stop(
            f"{label} expected once, "
            f"found {count}."
        )

    print(
        f"Patched: {label}"
    )

    return text.replace(
        old,
        new,
        1,
    )


print(
    "WOLF OS REVENUE TRUTH patch starting..."
)

for path in [
    APP,
    REVENUE,
]:
    if not path.exists():
        stop(
            f"Missing file: {path}"
        )

    backup = (
        BACKUP_DIR
        / (
            f"{path.stem}-"
            f"{STAMP}"
            f"{path.suffix}"
        )
    )

    shutil.copy2(
        path,
        backup,
    )

    print(
        f"Backup created: {backup}"
    )


app_text = APP.read_text(
    encoding="utf-8",
)

revenue_text = REVENUE.read_text(
    encoding="utf-8",
)


# =================================================
# REVENUE ORDER TYPE
# =================================================

offer_type = '''type Offer = {
  name: string;
  price: number;
  description: string;
};

'''

revenue_order_type = '''type RevenueOrder = {
  id?: string;
  payment_status?: string;
  total_cents?: number;
};

'''

if "type RevenueOrder =" not in revenue_text:
    revenue_text = replace_once(
        revenue_text,
        offer_type,
        revenue_order_type + offer_type,
        "RevenueOrder type",
    )
else:
    print(
        "RevenueOrder type already present."
    )


# =================================================
# LIVE ORDERS PROP
# =================================================

old_signature = (
    "export default function "
    "RevenueCommandCenter() {"
)

new_signature = '''export default function RevenueCommandCenter({
  orders,
}: {
  orders: RevenueOrder[];
}) {'''

revenue_text = replace_once(
    revenue_text,
    old_signature,
    new_signature,
    "Revenue Command Center orders prop",
)


# =================================================
# ENGINE STATUS COPY
# =================================================

old_status = '''      "Revenue Engine connected to the unified SQLite pipeline."
'''

new_status = '''      "Revenue Engine connected to unified SQLite pipeline state and live order payment status."
'''

revenue_text = replace_once(
    revenue_text,
    old_status,
    new_status,
    "Revenue Truth status copy",
)


# =================================================
# REAL REVENUE CALCULATIONS
# =================================================

old_math = '''  const wonRevenue =
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
'''

new_math = '''  const wonRevenue =
    wonDeals.reduce(
      (total, deal) =>
        total + deal.dealValue,
      0
    );

  const closedDeals =
    wonDeals.length;

  const orderValue =
    orders.reduce(
      (total, order) =>
        total +
        (
          Number(
            order.total_cents
          ) || 0
        ) / 100,
      0
    );

  const paidOrders =
    orders.filter(
      (order) =>
        String(
          order.payment_status || ""
        )
          .trim()
          .toLowerCase() === "paid"
    );

  const collectedRevenue =
    paidOrders.reduce(
      (total, order) =>
        total +
        (
          Number(
            order.total_cents
          ) || 0
        ) / 100,
      0
    );

  const outstandingRevenue =
    Math.max(
      0,
      orderValue -
        collectedRevenue
    );

  const remainingRevenue =
    Math.max(
      0,
      monthlyGoal -
        collectedRevenue
    );
'''

revenue_text = replace_once(
    revenue_text,
    old_math,
    new_math,
    "real order and payment calculations",
)


# =================================================
# REMOVE MISLEADING SECURED PROGRESS
# =================================================

old_progress = '''  const progress =
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

'''

revenue_text = replace_once(
    revenue_text,
    old_progress,
    "",
    "misleading secured progress calculation",
)


# =================================================
# REVENUE ATTACK PLAN LANGUAGE
# =================================================

old_sales_plan = '''          `Won revenue: ${money(wonRevenue)}`,
          `Modeled revenue: ${money(simulationRevenue)}`,
          `Revenue secured: ${money(securedRevenue)}`,
          `Revenue remaining: ${money(remainingRevenue)}`,
'''

new_sales_plan = '''          `Won pipeline value: ${money(wonRevenue)}`,
          `Order value: ${money(orderValue)}`,
          `Collected revenue: ${money(collectedRevenue)}`,
          `Outstanding revenue: ${money(outstandingRevenue)}`,
          `Modeled revenue, not collected: ${money(simulationRevenue)}`,
          `Cash goal remaining: ${money(remainingRevenue)}`,
'''

revenue_text = replace_once(
    revenue_text,
    old_sales_plan,
    new_sales_plan,
    "Revenue Attack Plan truth language",
)


old_dependencies = '''        wonRevenue,
        simulationRevenue,
        securedRevenue,
        remainingRevenue,
'''

new_dependencies = '''        wonRevenue,
        orderValue,
        collectedRevenue,
        outstandingRevenue,
        simulationRevenue,
        remainingRevenue,
'''

revenue_text = replace_once(
    revenue_text,
    old_dependencies,
    new_dependencies,
    "Revenue Attack Plan dependencies",
)


# =================================================
# HEADER TRUTH COPY
# =================================================

old_header_copy = '''            Live revenue intelligence
            calculated from the same SQLite
            pipeline used by Deal Desk and
            Priority Engine.
'''

new_header_copy = '''            Live revenue truth calculated
            from SQLite pipeline state and
            real order payment status.
'''

revenue_text = replace_once(
    revenue_text,
    old_header_copy,
    new_header_copy,
    "Revenue Truth header copy",
)

revenue_text = replace_once(
    revenue_text,
    "          SQLITE REVENUE SYNC",
    "          REVENUE TRUTH LIVE",
    "Revenue Truth live status",
)


# =================================================
# EXACT REVENUE COMMAND GRID REPLACEMENT
# =================================================

grid_start_marker = (
    '      <div className="revenue-command-grid">'
)

control_layout_marker = (
    '      <div className="revenue-control-layout">'
)

grid_start = revenue_text.find(
    grid_start_marker
)

if grid_start < 0:
    stop(
        "Revenue Command grid start not found."
    )

grid_end = revenue_text.find(
    control_layout_marker,
    grid_start,
)

if grid_end < 0:
    stop(
        "Revenue control layout boundary "
        "not found."
    )

if grid_end <= grid_start:
    stop(
        "Revenue Command grid boundary "
        "is invalid."
    )

print(
    "Located exact Revenue Command grid boundary."
)

truth_grid = '''      <div className="revenue-command-grid">
        <article className="revenue-gauge-card revenue-gauge-primary">
          <span>
            Won Pipeline Value
          </span>

          <strong>
            {money(wonRevenue)}
          </strong>

          <small>
            {closedDeals} won deal
            {closedDeals === 1
              ? ""
              : "s"}{" "}
            in the unified SQLite pipeline
          </small>
        </article>

        <article className="revenue-gauge-card">
          <span>
            Order Value
          </span>

          <strong>
            {money(orderValue)}
          </strong>

          <small>
            {orders.length} recorded order
            {orders.length === 1
              ? ""
              : "s"}
          </small>
        </article>

        <article className="revenue-gauge-card">
          <span>
            Collected Revenue
          </span>

          <strong>
            {money(collectedRevenue)}
          </strong>

          <small>
            {paidOrders.length} paid order
            {paidOrders.length === 1
              ? ""
              : "s"}{" "}
            · modeled revenue remains separate
          </small>
        </article>

        <article className="revenue-gauge-card">
          <span>
            Outstanding Revenue
          </span>

          <strong>
            {money(outstandingRevenue)}
          </strong>

          <small>
            Uncollected order value ·
            pipeline coverage {pipelineCoverage}%
          </small>
        </article>
      </div>

'''

revenue_text = (
    revenue_text[:grid_start]
    + truth_grid
    + revenue_text[grid_end:]
)

print(
    "Patched: Revenue Truth gauge grid"
)


# =================================================
# GLOBAL SAFE WORDING CLEANUP
# =================================================

revenue_text = revenue_text.replace(
    "Won revenue:",
    "Won pipeline value:",
)

revenue_text = revenue_text.replace(
    "Revenue secured",
    "Collected revenue",
)


# =================================================
# CONNECT APP ORDERS
# =================================================

app_text = replace_once(
    app_text,
    "<RevenueCommandCenter />",
    "<RevenueCommandCenter orders={orders} />",
    "App live orders connection",
)


# =================================================
# SAFETY VERIFICATION BEFORE WRITE
# =================================================

if "securedRevenue" in revenue_text:
    stop(
        "securedRevenue still exists after "
        "Revenue Truth rewrite."
    )

if "const progress =" in revenue_text:
    stop(
        "old progress calculation still exists."
    )

if (
    "<RevenueCommandCenter orders={orders} />"
    not in app_text
):
    stop(
        "Revenue Command Center orders prop "
        "was not connected."
    )

if "Won Pipeline Value" not in revenue_text:
    stop(
        "Won Pipeline Value metric is missing."
    )

if "Collected Revenue" not in revenue_text:
    stop(
        "Collected Revenue metric is missing."
    )

if "Outstanding Revenue" not in revenue_text:
    stop(
        "Outstanding Revenue metric is missing."
    )


# =================================================
# WRITE FILES
# =================================================

REVENUE.write_text(
    revenue_text,
    encoding="utf-8",
)

APP.write_text(
    app_text,
    encoding="utf-8",
)

print(
    "Revenue Truth source files written."
)


# =================================================
# FRONTEND BUILD
# =================================================

print()
print(
    "--- RUNNING FRONTEND BUILD ---"
)

result = subprocess.run(
    [
        "npm.cmd",
        "run",
        "build",
    ],
    cwd=FRONTEND,
    text=True,
)

if result.returncode != 0:
    stop(
        "Frontend build failed. "
        "Review the TypeScript error above."
    )


print()
print(
    "SUCCESS: WOLF OS REVENUE TRUTH INSTALLED."
)

print(
    "Won pipeline value, order value, "
    "collected revenue, and outstanding "
    "revenue now use separate live metrics."
)