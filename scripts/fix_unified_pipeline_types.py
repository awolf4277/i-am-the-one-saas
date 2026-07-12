from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND = ROOT / "frontend"

COMPONENTS = FRONTEND / "src" / "components"

PRIORITY = COMPONENTS / "PriorityEngine.tsx"
REVENUE = COMPONENTS / "RevenueCommandCenter.tsx"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Unified Pipeline TypeScript repair starting...")


def backup(path: Path, name: str) -> None:
    backup_dir = (
        ROOT
        / "backups"
        / "unified-pipeline-types"
    )

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


for path in [
    PRIORITY,
    REVENUE,
]:
    if not path.exists():
        raise SystemExit(
            f"Required file not found: {path}"
        )


backup(
    PRIORITY,
    "PriorityEngine",
)

backup(
    REVENUE,
    "RevenueCommandCenter",
)


print()
print("--- RESTORING PRIORITY ENGINE LOGIC ---")


priority = PRIORITY.read_text(
    encoding="utf-8"
)


priority_helpers = r'''function stageScore(stage: Stage) {
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

'''


if "function stageScore(" not in priority:
    anchor = "function copyFallback("

    position = priority.find(anchor)

    if position < 0:
        raise SystemExit(
            "Priority Engine copyFallback anchor not found."
        )

    priority = (
        priority[:position]
        + priority_helpers
        + priority[position:]
    )

    print(
        "Restored Priority Engine scoring helpers."
    )

else:
    print(
        "Priority Engine scoring helpers already exist."
    )


PRIORITY.write_text(
    priority,
    encoding="utf-8",
)


print()
print("--- REPAIRING REVENUE ENGINE TYPES ---")


revenue = REVENUE.read_text(
    encoding="utf-8"
)


old_import = '''import {
  useUnifiedPipeline,
} from "../lib/pipelineState";'''

new_import = '''import {
  type PipelineState,
  useUnifiedPipeline,
} from "../lib/pipelineState";'''


if old_import in revenue:
    revenue = replace_once(
        revenue,
        old_import,
        new_import,
        "Revenue PipelineState type import",
    )

elif "type PipelineState" in revenue:
    print(
        "Revenue PipelineState type already imported."
    )

else:
    raise SystemExit(
        "Revenue pipelineState import not found."
    )


old_values = '''  const pipelineDeals =
    Object.values(pipeline);'''

new_values = '''  const pipelineDeals =
    Object.values(
      pipeline
    ) as PipelineState[];'''


if old_values in revenue:
    revenue = replace_once(
        revenue,
        old_values,
        new_values,
        "typed SQLite pipeline values",
    )

elif "as PipelineState[]" in revenue:
    print(
        "Revenue pipeline values already typed."
    )

else:
    raise SystemExit(
        "Revenue Object.values pipeline block not found."
    )


REVENUE.write_text(
    revenue,
    encoding="utf-8",
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
        "Frontend build still failed. "
        "Review the TypeScript error above."
    )


print()
print(
    "SUCCESS: UNIFIED PIPELINE TYPESCRIPT REPAIRED."
)

print(
    "Priority Engine scoring logic restored."
)

print(
    "Revenue Engine pipeline values are strongly typed."
)

print(
    "Unified SQLite state architecture remains installed."
)

print(
    "Restart WOLF OS and test full system synchronization."
)