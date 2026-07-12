from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys

ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND = ROOT / "frontend"
COMPONENTS = FRONTEND / "src" / "components"

COMPONENT = COMPONENTS / "PriorityEngine.tsx"
CSS = COMPONENTS / "PriorityEngine.css"

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

print("WOLF OS Priority Execution Feedback patch starting...")


def backup(path: Path, name: str) -> Path:
    backup_dir = ROOT / "backups" / "priority-feedback"

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


if not COMPONENT.exists():
    raise SystemExit(
        f"PriorityEngine not found: {COMPONENT}"
    )

if not CSS.exists():
    raise SystemExit(
        f"PriorityEngine CSS not found: {CSS}"
    )


backup(
    COMPONENT,
    "PriorityEngine",
)

backup(
    CSS,
    "PriorityEngine-css",
)


component = COMPONENT.read_text(
    encoding="utf-8"
)


component = replace_once(
    component,
    'import { useEffect, useMemo, useState } from "react";',
    'import { useEffect, useMemo, useRef, useState } from "react";',
    "React feedback imports",
)


target_type = '''type RankedTarget = {
  lead: Lead;
  deal: PipelineState;
  score: number;
  priority: string;
  reason: string;
  nextMove: string;
};
'''

feedback_type = '''type RankedTarget = {
  lead: Lead;
  deal: PipelineState;
  score: number;
  priority: string;
  reason: string;
  nextMove: string;
};

type FeedbackState =
  | "idle"
  | "locking"
  | "executed"
  | "closing"
  | "error";
'''

component = replace_once(
    component,
    target_type,
    feedback_type,
    "execution feedback state type",
)


old_execution_state = '''  const [executing, setExecuting] =
    useState(false);

  const leads = useMemo<Lead[]>(() => {'''

new_execution_state = '''  const [executing, setExecuting] =
    useState(false);

  const [feedbackState, setFeedbackState] =
    useState<FeedbackState>("idle");

  const [feedbackMessage, setFeedbackMessage] =
    useState("SYSTEM READY");

  const feedbackTimer =
    useRef<number | null>(null);

  const showFeedback = (
    state: FeedbackState,
    message: string,
    duration = 2200
  ) => {
    if (feedbackTimer.current !== null) {
      window.clearTimeout(
        feedbackTimer.current
      );
    }

    setFeedbackState(state);
    setFeedbackMessage(message);

    if (state !== "locking") {
      feedbackTimer.current =
        window.setTimeout(() => {
          setFeedbackState("idle");
          setFeedbackMessage(
            "SYSTEM READY"
          );

          feedbackTimer.current = null;
        }, duration);
    }
  };

  useEffect(() => {
    return () => {
      if (
        feedbackTimer.current !== null
      ) {
        window.clearTimeout(
          feedbackTimer.current
        );
      }
    };
  }, []);

  const leads = useMemo<Lead[]>(() => {'''

component = replace_once(
    component,
    old_execution_state,
    new_execution_state,
    "execution feedback controls",
)


old_closing = '''      if (
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
'''

new_closing = '''      if (
        target.deal.stage ===
        "Closing"
      ) {
        showFeedback(
          "closing",
          "CLOSING MODE · CLOSE MESSAGE ARMED",
          2800
        );

        await copyTargetMessage(
          target
        );

        setStatus(
          `${target.lead.business} is at CLOSING. Close message copied. Ask for the deposit before marking the deal Won.`
        );

        return;
      }
'''

component = replace_once(
    component,
    old_closing,
    new_closing,
    "closing mode feedback",
)


old_executing = '''      setExecuting(true);

      setStatus(
        `Executing next move for ${target.lead.business}...`
      );

      try {
'''

new_executing = '''      setExecuting(true);

      showFeedback(
        "locking",
        `TARGET LOCK · ${target.lead.business.toUpperCase()}`
      );

      setStatus(
        `Executing next move for ${target.lead.business}...`
      );

      try {
'''

component = replace_once(
    component,
    old_executing,
    new_executing,
    "target lock feedback",
)


old_success = '''        setStatus(
          `${target.lead.business} advanced from ${target.deal.stage} to ${nextStage}. Priority Engine recalculated the attack queue.`
        );
      } catch (error) {
        setStatus(
'''

new_success = '''        showFeedback(
          "executed",
          `MOVE EXECUTED · ${target.deal.stage.toUpperCase()} → ${nextStage.toUpperCase()}`,
          2800
        );

        setStatus(
          `${target.lead.business} advanced from ${target.deal.stage} to ${nextStage}. Priority Engine recalculated the attack queue.`
        );
      } catch (error) {
        showFeedback(
          "error",
          "EXECUTION FAILED · CHECK SYSTEM",
          3200
        );

        setStatus(
'''

component = replace_once(
    component,
    old_success,
    new_success,
    "move executed feedback",
)


old_target_card = '''        <article className="priority-primary-target">
          <div className="priority-target-number">
            TARGET 01
          </div>
'''

new_target_card = '''        <article
          className={`priority-primary-target feedback-${feedbackState}`}
        >
          <div
            className={`priority-execution-feedback ${feedbackState}`}
          >
            <span className="priority-feedback-light" />

            <strong>
              {feedbackMessage}
            </strong>
          </div>

          <div className="priority-execution-sweep" />

          <div className="priority-target-number">
            TARGET 01
          </div>
'''

component = replace_once(
    component,
    old_target_card,
    new_target_card,
    "execution feedback display",
)


old_button_text = '''              {executing
                ? "EXECUTING..."
                : "EXECUTE NEXT MOVE"}
'''

new_button_text = '''              {executing
                ? feedbackState === "locking"
                  ? "TARGET LOCK..."
                  : "EXECUTING..."
                : "EXECUTE NEXT MOVE"}
'''

component = replace_once(
    component,
    old_button_text,
    new_button_text,
    "execution button feedback",
)


COMPONENT.write_text(
    component,
    encoding="utf-8",
)

print(
    "Priority Engine execution sequence patched."
)


css = CSS.read_text(
    encoding="utf-8"
)

feedback_css = r'''

/* WOLF OS PRIORITY EXECUTION FEEDBACK */

.priority-primary-target {
  position: relative;
  overflow: hidden;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.priority-execution-feedback {
  position: relative;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 15px;
  padding: 8px 11px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.28);
  color: rgba(239, 243, 249, 0.56);
  font-size: 0.67rem;
  font-weight: 950;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  transition:
    color 180ms ease,
    border-color 180ms ease,
    background 180ms ease,
    box-shadow 180ms ease;
}

.priority-feedback-light {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
}

.priority-execution-feedback.locking {
  border-color: rgba(255, 95, 54, 0.58);
  background: rgba(184, 39, 20, 0.2);
  color: #ff866f;
  box-shadow: 0 0 25px rgba(255, 63, 35, 0.14);
}

.priority-execution-feedback.locking
.priority-feedback-light {
  background: #ff5037;
  box-shadow: 0 0 17px #ff5037;
  animation: priority-lock-light 420ms ease-in-out infinite alternate;
}

.priority-execution-feedback.executed {
  border-color: rgba(73, 255, 162, 0.58);
  background: rgba(31, 151, 87, 0.19);
  color: #74ffb5;
  box-shadow: 0 0 29px rgba(64, 255, 156, 0.16);
}

.priority-execution-feedback.executed
.priority-feedback-light {
  background: #62ffa9;
  box-shadow: 0 0 19px #62ffa9;
}

.priority-execution-feedback.closing {
  border-color: rgba(255, 185, 64, 0.55);
  background: rgba(173, 99, 16, 0.18);
  color: #ffc66c;
}

.priority-execution-feedback.closing
.priority-feedback-light {
  background: #ffb63e;
  box-shadow: 0 0 19px #ffb63e;
}

.priority-execution-feedback.error {
  border-color: rgba(255, 68, 68, 0.65);
  background: rgba(170, 24, 24, 0.22);
  color: #ff7777;
}

.priority-execution-feedback.error
.priority-feedback-light {
  background: #ff3d3d;
  box-shadow: 0 0 19px #ff3d3d;
}

.priority-execution-sweep {
  position: absolute;
  z-index: 1;
  top: 0;
  bottom: 0;
  left: -35%;
  width: 24%;
  opacity: 0;
  transform: skewX(-18deg);
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 89, 51, 0.15),
    rgba(255, 149, 84, 0.28),
    transparent
  );
  pointer-events: none;
}

.feedback-locking {
  border-color: rgba(255, 81, 49, 0.68);
  box-shadow:
    0 0 0 1px rgba(255, 69, 39, 0.15),
    0 0 42px rgba(255, 49, 27, 0.16);
}

.feedback-locking
.priority-execution-sweep {
  opacity: 1;
  animation: priority-target-scan 720ms linear infinite;
}

.feedback-executed {
  border-color: rgba(82, 255, 165, 0.7);
  animation: priority-execution-hit 700ms ease;
  box-shadow:
    0 0 0 1px rgba(75, 255, 160, 0.16),
    0 0 48px rgba(65, 255, 153, 0.18);
}

.feedback-executed
.priority-money strong {
  animation: priority-money-surge 850ms ease;
}

.feedback-closing {
  border-color: rgba(255, 184, 65, 0.63);
  box-shadow:
    0 0 0 1px rgba(255, 178, 55, 0.13),
    0 0 45px rgba(255, 145, 33, 0.14);
}

.feedback-error {
  border-color: rgba(255, 65, 65, 0.72);
  animation: priority-system-error 320ms ease 2;
}

@keyframes priority-lock-light {
  from {
    opacity: 0.4;
    transform: scale(0.8);
  }

  to {
    opacity: 1;
    transform: scale(1.25);
  }
}

@keyframes priority-target-scan {
  from {
    left: -35%;
  }

  to {
    left: 125%;
  }
}

@keyframes priority-execution-hit {
  0% {
    transform: scale(1);
  }

  35% {
    transform: scale(1.012);
  }

  100% {
    transform: scale(1);
  }
}

@keyframes priority-money-surge {
  0% {
    transform: scale(1);
  }

  35% {
    transform: scale(1.12);
    filter: brightness(1.8);
  }

  100% {
    transform: scale(1);
    filter: brightness(1);
  }
}

@keyframes priority-system-error {
  0%,
  100% {
    transform: translateX(0);
  }

  35% {
    transform: translateX(-4px);
  }

  70% {
    transform: translateX(4px);
  }
}
'''

if (
    "WOLF OS PRIORITY EXECUTION FEEDBACK"
    not in css
):
    css += feedback_css

    print(
        "Added Priority Engine reaction animations."
    )

else:
    print(
        "Priority feedback CSS already installed."
    )


CSS.write_text(
    css,
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
        "Frontend build failed. Review the TypeScript error above."
    )


print()
print(
    "SUCCESS: PRIORITY EXECUTION FEEDBACK INSTALLED."
)
print(
    "Execute Next Move now triggers target lock, execution hit, and recalculated queue feedback."
)
print(
    "Closing mode now visibly arms the close-message sequence."
)
print(
    "Refresh Owner Console and fire EXECUTE NEXT MOVE."
)