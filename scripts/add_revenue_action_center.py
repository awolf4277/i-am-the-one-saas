from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(r"X:\i-am-the-one-saas")
TSX_PATH = ROOT / "frontend" / "src" / "components" / "PriorityEngine.tsx"
CSS_PATH = ROOT / "frontend" / "src" / "components" / "PriorityEngine.css"
FRONTEND_DIR = ROOT / "frontend"

MARKER = "WOLF OS REVENUE ACTION CENTER"
CSS_MARKER = "WOLF OS REVENUE ACTION CENTER STYLES"


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected exactly 1 match, found {count}. No files were changed.")
    return text.replace(old, new, 1)


def regex_replace_once(
    text: str,
    pattern: str,
    replacement: str,
    label: str,
    flags: int = 0,
) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        fail(f"{label}: expected exactly 1 match, found {count}. No files were changed.")
    return updated


def main() -> int:
    print("WOLF OS Revenue Action Center patch starting...")

    if not TSX_PATH.exists():
        fail(f"Priority Engine not found: {TSX_PATH}")

    if not CSS_PATH.exists():
        fail(f"Priority Engine CSS not found: {CSS_PATH}")

    tsx = TSX_PATH.read_text(encoding="utf-8")
    css = CSS_PATH.read_text(encoding="utf-8")

    if MARKER in tsx or CSS_MARKER in css:
        print("Revenue Action Center is already installed. Nothing changed.")
        return 0

    # 1. Add the selected action target state.
    old_state = '''  const [executing, setExecuting] =
    useState(false);

  const [feedbackState, setFeedbackState] ='''
    new_state = '''  const [executing, setExecuting] =
    useState(false);

  // WOLF OS REVENUE ACTION CENTER
  const [actionTarget, setActionTarget] =
    useState<RankedTarget | null>(null);

  const [feedbackState, setFeedbackState] ='''
    tsx = replace_once(
        tsx,
        old_state,
        new_state,
        "Add Revenue Action Center state",
    )

    # 2. Add Escape-key support for the action center.
    cleanup_effect = '''  useEffect(() => {
    return () => {
      if (
        feedbackTimer.current !== null
      ) {
        window.clearTimeout(
          feedbackTimer.current
        );
      }
    };
  }, []);'''
    cleanup_with_dialog_effect = cleanup_effect + '''

  useEffect(() => {
    if (!actionTarget) {
      return;
    }

    const onKeyDown = (
      event: KeyboardEvent
    ) => {
      if (event.key === "Escape") {
        setActionTarget(null);
      }
    };

    document.addEventListener(
      "keydown",
      onKeyDown
    );

    return () => {
      document.removeEventListener(
        "keydown",
        onKeyDown
      );
    };
  }, [actionTarget]);'''
    tsx = replace_once(
        tsx,
        cleanup_effect,
        cleanup_with_dialog_effect,
        "Add action-center keyboard behavior",
    )

    # 3. De-prioritize deals after the owner completes an action and the buyer is pending.
    old_score = '''          const score =
            stageScore(
              deal.stage
            ) +
            timelineScore(
              lead.timeline
            ) +
            valueScore;'''
    new_score = '''          const waitingForBuyer =
            deal.nextAction.startsWith(
              "WAITING · "
            );

          const waitingPenalty =
            waitingForBuyer
              ? 120
              : 0;

          const score =
            stageScore(
              deal.stage
            ) +
            timelineScore(
              lead.timeline
            ) +
            valueScore -
            waitingPenalty;'''
    tsx = replace_once(
        tsx,
        old_score,
        new_score,
        "Add waiting-for-buyer scoring",
    )

    old_ranked_result = '''            reason: reasonFor(
              lead,
              deal
            ),
            nextMove: nextMoveFor(
              deal.stage
            ),'''
    new_ranked_result = '''            reason:
              waitingForBuyer
                ? "owner action completed · waiting on buyer response"
                : reasonFor(
                    lead,
                    deal
                  ),
            nextMove:
              waitingForBuyer
                ? deal.nextAction.replace(
                    "WAITING · ",
                    ""
                  )
                : nextMoveFor(
                    deal.stage
                  ),'''
    tsx = replace_once(
        tsx,
        old_ranked_result,
        new_ranked_result,
        "Expose waiting state in ranked targets",
    )

    # 4. Add action-center open/close helpers.
    execute_anchor = '''  const executeNextMove =
    async (
      target: RankedTarget
    ) => {'''
    action_helpers = '''  const openActionCenter = (
    target: RankedTarget
  ) => {
    setActionTarget(target);

    showFeedback(
      target.deal.stage === "Closing"
        ? "closing"
        : "locking",
      `ACTION CENTER · ${target.lead.business.toUpperCase()}`,
      1800
    );

    setStatus(
      `${target.lead.business} loaded into the Revenue Action Center.`
    );
  };

  const closeActionCenter = () => {
    if (executing) {
      return;
    }

    setActionTarget(null);
  };

'''
    if execute_anchor not in tsx:
        fail("Execution routine anchor was not found. No files were changed.")
    tsx = tsx.replace(execute_anchor, action_helpers + execute_anchor, 1)

    # 5. Replace execution behavior.
    execute_pattern = r'''  const executeNextMove =\s*
    async \(\s*
      target: RankedTarget\s*
    \) => \{.*?\n    \};\n\n  if \(!primaryTarget\) \{'''
    execute_replacement = '''  const executeNextMove =
    async (
      target: RankedTarget
    ) => {
      if (executing) {
        return;
      }

      const ownerToken =
        window.localStorage.getItem(
          "wolf_owner_token"
        ) || "";

      if (!ownerToken) {
        setStatus(
          "Unlock Owner Console before executing the priority move."
        );

        return;
      }

      const isClosing =
        target.deal.stage ===
        "Closing";

      const currentIndex =
        stages.indexOf(
          target.deal.stage
        );

      const nextStage =
        isClosing
          ? target.deal.stage
          : stages[
              Math.min(
                currentIndex + 1,
                stages.indexOf(
                  "Closing"
                )
              )
            ];

      const completionTime =
        new Date().toLocaleString();

      const nextDeal: PipelineState =
        {
          ...target.deal,
          stage: nextStage,
          nextAction:
            isClosing
              ? `WAITING · Deposit request sent ${completionTime}. Confirm payment, then mark the deal Won in Deal Desk.`
              : nextMoveFor(
                  nextStage
                ),
        };

      setExecuting(true);

      showFeedback(
        "locking",
        `LOGGING ACTION · ${target.lead.business.toUpperCase()}`
      );

      setStatus(
        `Saving completed action for ${target.lead.business}...`
      );

      try {
        await saveUnifiedPipelineDeal(
          target.lead.key,
          nextDeal,
          ownerToken
        );

        setActionTarget(null);

        showFeedback(
          "executed",
          isClosing
            ? "REQUEST SENT · BUYER RESPONSE PENDING"
            : `MOVE COMPLETE · ${target.deal.stage.toUpperCase()} → ${nextStage.toUpperCase()}`,
          3000
        );

        setStatus(
          isClosing
            ? `${target.lead.business} deposit request was logged in SQLite. WOLF OS moved to the next actionable buyer while payment is pending.`
            : `${target.lead.business} action completed. Deal advanced from ${target.deal.stage} to ${nextStage}, and the attack queue was recalculated.`
        );
      } catch (error) {
        showFeedback(
          "error",
          "EXECUTION FAILED · CHECK SYSTEM",
          3200
        );

        setStatus(
          error instanceof Error
            ? `Priority Engine error: ${error.message}`
            : "Priority action failed."
        );
      } finally {
        setExecuting(false);
      }
    };

  if (!primaryTarget) {'''
    tsx = regex_replace_once(
        tsx,
        execute_pattern,
        execute_replacement,
        "Replace Priority Engine execution flow",
        flags=re.DOTALL,
    )

    # 6. Remove duplicated EXECUTE wording and make the button open the action center.
    tsx = regex_replace_once(
        tsx,
        r'''<span>\s*EXECUTE NEXT MOVE\s*</span>''',
        '''<span>
              RECOMMENDED MOVE
            </span>''',
        "Rename recommended-move label",
    )

    tsx = regex_replace_once(
        tsx,
        r'''onClick=\{\(\) =>\s*
\s*void executeNextMove\(\s*
\s*primaryTarget\s*
\s*\)\s*
\s*\}''',
        '''onClick={() =>
                openActionCenter(
                  primaryTarget
                )
              }''',
        "Wire primary button to Revenue Action Center",
    )

    tsx = replace_once(
        tsx,
        ': "EXECUTE NEXT MOVE"}',
        ': "OPEN ACTION CENTER"}',
        "Rename primary action button",
    )

    # 7. Add the Revenue Action Center dialog to the main Priority Engine section.
    action_center_markup = r'''
      {actionTarget && (
        <div
          className="revenue-action-backdrop"
          role="presentation"
          onMouseDown={
            closeActionCenter
          }
        >
          <div
            className="revenue-action-center"
            role="dialog"
            aria-modal="true"
            aria-labelledby="revenue-action-title"
            onMouseDown={(event) =>
              event.stopPropagation()
            }
          >
            <div className="revenue-action-scanline" />

            <header className="revenue-action-header">
              <div>
                <p className="priority-engine-kicker">
                  WOLF OS™ REVENUE ACTION CENTER
                </p>

                <h3 id="revenue-action-title">
                  {actionTarget.lead.business}
                </h3>

                <p>
                  Execute the recommended move,
                  contact the buyer, and log the
                  completed action into SQLite.
                </p>
              </div>

              <button
                type="button"
                className="revenue-action-close"
                onClick={
                  closeActionCenter
                }
                disabled={executing}
                aria-label="Close Revenue Action Center"
              >
                ×
              </button>
            </header>

            <div className="revenue-action-metrics">
              <div>
                <span>CURRENT STAGE</span>
                <strong>
                  {actionTarget.deal.stage}
                </strong>
              </div>

              <div>
                <span>MONEY AT STAKE</span>
                <strong>
                  {money(
                    actionTarget.deal.dealValue
                  )}
                </strong>
              </div>

              <div>
                <span>BUYER TIMELINE</span>
                <strong>
                  {actionTarget.lead.timeline}
                </strong>
              </div>
            </div>

            <div className="revenue-action-directive">
              <span>WOLF OS DIRECTIVE</span>

              <strong>
                {actionTarget.nextMove}
              </strong>

              <p>
                {actionTarget.reason}
              </p>
            </div>

            <label className="revenue-action-message">
              <span>
                READY-TO-SEND BUYER MESSAGE
              </span>

              <textarea
                readOnly
                value={
                  buildCloseMessage(
                    actionTarget
                  )
                }
              />
            </label>

            <div className="revenue-action-controls">
              <button
                type="button"
                onClick={() =>
                  void copyTargetMessage(
                    actionTarget
                  )
                }
              >
                COPY MESSAGE
              </button>

              <button
                type="button"
                onClick={() =>
                  openTargetEmail(
                    actionTarget
                  )
                }
              >
                OPEN EMAIL
              </button>

              <button
                type="button"
                className="revenue-action-complete"
                disabled={executing}
                onClick={() =>
                  void executeNextMove(
                    actionTarget
                  )
                }
              >
                {executing
                  ? "LOGGING ACTION..."
                  : actionTarget.deal.stage ===
                      "Closing"
                    ? "MARK REQUEST SENT"
                    : "MARK ACTION COMPLETE"}
              </button>
            </div>

            <p className="revenue-action-footnote">
              Completion is persisted through the
              unified SQLite pipeline and immediately
              refreshes the Priority Engine, Deal Desk,
              Revenue Engine, and activity timeline.
            </p>
          </div>
        </div>
      )}
'''
    closing_index = tsx.rfind("    </section>")
    if closing_index < 0:
        fail("Main Priority Engine closing section was not found. No files were changed.")
    tsx = tsx[:closing_index] + action_center_markup + tsx[closing_index:]

    # 8. Append isolated styles.
    css += r'''

/* WOLF OS REVENUE ACTION CENTER STYLES */
.revenue-action-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 50% 15%, rgba(80, 160, 255, 0.18), transparent 42%),
    rgba(2, 7, 14, 0.88);
  backdrop-filter: blur(10px);
}

.revenue-action-center {
  position: relative;
  width: min(840px, 100%);
  max-height: min(880px, calc(100vh - 48px));
  overflow: auto;
  border: 1px solid rgba(124, 204, 255, 0.34);
  border-radius: 24px;
  padding: 26px;
  background:
    linear-gradient(145deg, rgba(13, 24, 38, 0.98), rgba(4, 10, 18, 0.99));
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.035) inset,
    0 28px 90px rgba(0, 0, 0, 0.72),
    0 0 54px rgba(43, 157, 255, 0.14);
}

.revenue-action-scanline {
  position: absolute;
  inset: 0 0 auto;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(122, 218, 255, 0.95), transparent);
  box-shadow: 0 0 22px rgba(92, 196, 255, 0.8);
  animation: revenueActionSweep 2.8s ease-in-out infinite;
  pointer-events: none;
}

.revenue-action-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 22px;
}

.revenue-action-header h3 {
  margin: 4px 0 8px;
  font-size: clamp(1.65rem, 4vw, 2.45rem);
  letter-spacing: -0.04em;
}

.revenue-action-header p {
  margin: 0;
  max-width: 650px;
  color: rgba(225, 237, 247, 0.7);
  line-height: 1.6;
}

.revenue-action-close {
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.055);
  color: #ffffff;
  font-size: 1.65rem;
  line-height: 1;
  cursor: pointer;
}

.revenue-action-close:hover {
  border-color: rgba(129, 218, 255, 0.72);
  background: rgba(89, 180, 255, 0.13);
}

.revenue-action-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.revenue-action-metrics > div,
.revenue-action-directive,
.revenue-action-message {
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.035);
}

.revenue-action-metrics > div {
  padding: 15px;
}

.revenue-action-metrics span,
.revenue-action-directive > span,
.revenue-action-message > span {
  display: block;
  margin-bottom: 7px;
  color: rgba(147, 214, 255, 0.72);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.revenue-action-metrics strong {
  display: block;
  overflow-wrap: anywhere;
  font-size: 1rem;
}

.revenue-action-directive {
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: 0 0 34px rgba(62, 161, 255, 0.07) inset;
}

.revenue-action-directive strong {
  display: block;
  font-size: 1.15rem;
  line-height: 1.45;
}

.revenue-action-directive p {
  margin: 9px 0 0;
  color: rgba(225, 237, 247, 0.64);
}

.revenue-action-message {
  display: block;
  padding: 16px;
}

.revenue-action-message textarea {
  width: 100%;
  min-height: 260px;
  resize: vertical;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 12px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.24);
  color: rgba(245, 250, 255, 0.92);
  font: inherit;
  line-height: 1.55;
}

.revenue-action-message textarea:focus {
  outline: 1px solid rgba(119, 213, 255, 0.7);
  box-shadow: 0 0 0 4px rgba(64, 168, 255, 0.08);
}

.revenue-action-controls {
  display: grid;
  grid-template-columns: 1fr 1fr 1.35fr;
  gap: 12px;
  margin-top: 16px;
}

.revenue-action-controls button {
  min-height: 48px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.055);
  color: #ffffff;
  font-weight: 850;
  letter-spacing: 0.04em;
  cursor: pointer;
}

.revenue-action-controls button:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(126, 215, 255, 0.65);
  background: rgba(78, 171, 255, 0.12);
}

.revenue-action-controls .revenue-action-complete {
  border-color: rgba(99, 231, 164, 0.4);
  background:
    linear-gradient(135deg, rgba(32, 177, 111, 0.9), rgba(18, 114, 78, 0.94));
  box-shadow: 0 10px 30px rgba(22, 151, 95, 0.2);
}

.revenue-action-controls button:disabled {
  opacity: 0.58;
  cursor: wait;
}

.revenue-action-footnote {
  margin: 14px 2px 0;
  color: rgba(217, 231, 242, 0.55);
  font-size: 0.8rem;
  line-height: 1.55;
}

@keyframes revenueActionSweep {
  0%,
  100% {
    opacity: 0.35;
    transform: translateX(-28%);
  }

  50% {
    opacity: 1;
    transform: translateX(28%);
  }
}

@media (max-width: 720px) {
  .revenue-action-backdrop {
    align-items: end;
    padding: 10px;
  }

  .revenue-action-center {
    max-height: calc(100vh - 20px);
    border-radius: 20px 20px 14px 14px;
    padding: 20px 16px;
  }

  .revenue-action-metrics,
  .revenue-action-controls {
    grid-template-columns: 1fr;
  }

  .revenue-action-message textarea {
    min-height: 230px;
  }
}
'''

    # All validations passed: create backups and write.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tsx_backup = TSX_PATH.with_name(
        f"{TSX_PATH.stem}.before-revenue-action-center-{stamp}{TSX_PATH.suffix}"
    )
    css_backup = CSS_PATH.with_name(
        f"{CSS_PATH.stem}.before-revenue-action-center-{stamp}{CSS_PATH.suffix}"
    )

    shutil.copy2(TSX_PATH, tsx_backup)
    shutil.copy2(CSS_PATH, css_backup)

    TSX_PATH.write_text(tsx, encoding="utf-8")
    CSS_PATH.write_text(css, encoding="utf-8")

    print(f"Backup created: {tsx_backup}")
    print(f"Backup created: {css_backup}")
    print("Revenue Action Center TSX and CSS installed.")

    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        print("npm was not found. Patch installed, but the frontend build was not run.")
        return 0

    print("\nRunning frontend build...\n")
    result = subprocess.run(
        [npm, "run", "build"],
        cwd=FRONTEND_DIR,
        check=False,
    )

    if result.returncode != 0:
        print("\nFrontend build failed.")
        print("The patch remains installed and the backups above are available.")
        return result.returncode

    print("\nWOLF OS Revenue Action Center installed successfully.")
    print("Refresh the Owner Console with Ctrl+F5.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"\nPATCH STOPPED: {error}", file=sys.stderr)
        raise SystemExit(1)