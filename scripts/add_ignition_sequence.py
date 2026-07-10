from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
APP_PATH = FRONTEND_ROOT / "src" / "App.tsx"
CSS_PATH = FRONTEND_ROOT / "src" / "styles.css"


IGNITION_COMPONENT = r'''

function WolfIgnitionSequence({
  onComplete
}: {
  onComplete: () => void;
}) {
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("Initializing WOLF Core...");

  useEffect(() => {
    const start = performance.now();
    const duration = 3100;

    const frame = (now: number) => {
      const elapsed = now - start;
      const nextProgress = Math.min(100, Math.round((elapsed / duration) * 100));

      setProgress(nextProgress);

      if (nextProgress < 22) {
        setMessage("Initializing WOLF Core...");
      } else if (nextProgress < 46) {
        setMessage("Connecting Live API...");
      } else if (nextProgress < 68) {
        setMessage("Synchronizing Inventory...");
      } else if (nextProgress < 88) {
        setMessage("Loading Cockpit...");
      } else if (nextProgress < 100) {
        setMessage("Arming Launch Systems...");
      } else {
        setMessage("ENGINE ONLINE");
      }

      if (elapsed < duration) {
        window.requestAnimationFrame(frame);
      } else {
        window.setTimeout(onComplete, 350);
      }
    };

    const animationFrame = window.requestAnimationFrame(frame);

    return () => {
      window.cancelAnimationFrame(animationFrame);
    };
  }, [onComplete]);

  return (
    <div className="wolf-ignition-overlay" role="status" aria-live="polite">
      <div className="ignition-speed-lines" />

      <div className="ignition-panel">
        <div className="ignition-brand">
          <span className="ignition-mark">W</span>

          <div>
            <p>WOLF OS™</p>
            <small>I AM THE ONE™ SaaS v3.1</small>
          </div>
        </div>

        <div className="ignition-tree" aria-hidden="true">
          <span className={progress >= 15 ? "active" : ""} />
          <span className={progress >= 32 ? "active" : ""} />
          <span className={progress >= 49 ? "active amber" : ""} />
          <span className={progress >= 66 ? "active amber" : ""} />
          <span className={progress >= 83 ? "active amber" : ""} />
          <span className={progress >= 98 ? "active green" : ""} />
        </div>

        <div className="ignition-copy">
          <p className="ignition-kicker">TOP FUEL STARTUP SEQUENCE</p>
          <h1>{message}</h1>

          <div className="ignition-progress-track">
            <div
              className="ignition-progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="ignition-progress-meta">
            <span>{progress}%</span>
            <span>3.10 SEC BOOT</span>
          </div>
        </div>

        <div className="ignition-readouts">
          <div>
            <span>API</span>
            <strong>{progress >= 46 ? "CONNECTED" : "CHECKING"}</strong>
          </div>

          <div>
            <span>INVENTORY</span>
            <strong>{progress >= 68 ? "SYNCED" : "LOADING"}</strong>
          </div>

          <div>
            <span>COCKPIT</span>
            <strong>{progress >= 88 ? "ARMED" : "STANDBY"}</strong>
          </div>

          <div>
            <span>ENGINE</span>
            <strong>{progress >= 100 ? "ONLINE" : "IGNITION"}</strong>
          </div>
        </div>
      </div>
    </div>
  );
}

'''


IGNITION_STATE = r'''
  const [showIgnition, setShowIgnition] = useState(() => {
    if (typeof window === "undefined") return true;

    return window.sessionStorage.getItem("wolf_ignition_complete") !== "true";
  });

  const completeIgnition = () => {
    window.sessionStorage.setItem("wolf_ignition_complete", "true");
    setShowIgnition(false);
  };

'''


IGNITION_RENDER = r'''
      {showIgnition ? (
        <WolfIgnitionSequence onComplete={completeIgnition} />
      ) : null}

'''


IGNITION_CSS = r'''

/* WOLF OS 3.1-second ignition sequence */
.wolf-ignition-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: grid;
  place-items: center;
  padding: 24px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 35%, rgba(125, 255, 189, 0.14), transparent 34%),
    radial-gradient(circle at 50% 100%, rgba(255, 208, 87, 0.12), transparent 40%),
    linear-gradient(180deg, #05070a, #000000);
}

.ignition-speed-lines {
  position: absolute;
  inset: -20%;
  background:
    repeating-linear-gradient(
      90deg,
      transparent 0,
      transparent 80px,
      rgba(255, 255, 255, 0.025) 81px,
      transparent 82px
    );
  transform: perspective(700px) rotateX(62deg) translateY(25%);
  animation: ignitionRoad 900ms linear infinite;
}

.ignition-panel {
  position: relative;
  z-index: 2;
  width: min(940px, 100%);
  padding: 34px;
  border: 1px solid rgba(125, 255, 189, 0.2);
  border-radius: 32px;
  background:
    radial-gradient(circle at 10% 0%, rgba(125, 255, 189, 0.15), transparent 36%),
    radial-gradient(circle at 90% 10%, rgba(255, 208, 87, 0.12), transparent 32%),
    linear-gradient(135deg, rgba(255,255,255,0.075), rgba(255,255,255,0.02)),
    rgba(0, 0, 0, 0.78);
  box-shadow:
    0 50px 160px rgba(0, 0, 0, 0.72),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(18px);
}

.ignition-brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ignition-mark {
  width: 52px;
  height: 52px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  border: 1px solid rgba(125, 255, 189, 0.25);
  background: rgba(125, 255, 189, 0.08);
  color: #7dffbd;
  font-size: 1.6rem;
  font-weight: 950;
  box-shadow: 0 0 28px rgba(125, 255, 189, 0.18);
}

.ignition-brand p,
.ignition-brand small {
  display: block;
  margin: 0;
}

.ignition-brand p {
  color: rgba(255,255,255,0.96);
  font-weight: 950;
  letter-spacing: 0.12em;
}

.ignition-brand small {
  margin-top: 4px;
  color: rgba(255,255,255,0.5);
  font-weight: 800;
  letter-spacing: 0.08em;
}

.ignition-tree {
  display: grid;
  grid-template-columns: repeat(6, 18px);
  gap: 8px;
  margin: 28px 0;
}

.ignition-tree span {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
}

.ignition-tree span.active {
  background: rgba(255,255,255,0.95);
  box-shadow: 0 0 18px rgba(255,255,255,0.5);
}

.ignition-tree span.active.amber {
  background: #ffd057;
  box-shadow: 0 0 22px rgba(255, 208, 87, 0.58);
}

.ignition-tree span.active.green {
  background: #7dffbd;
  box-shadow:
    0 0 22px rgba(125, 255, 189, 0.68),
    0 0 46px rgba(125, 255, 189, 0.3);
}

.ignition-copy {
  margin-top: 14px;
}

.ignition-kicker {
  margin: 0 0 10px;
  color: #ffd057;
  font-size: 0.76rem;
  font-weight: 950;
  letter-spacing: 0.2em;
}

.ignition-copy h1 {
  margin: 0;
  font-size: clamp(2rem, 6vw, 4.8rem);
  line-height: 0.96;
  letter-spacing: -0.075em;
  text-transform: uppercase;
}

.ignition-progress-track {
  height: 12px;
  margin-top: 28px;
  overflow: hidden;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.06);
}

.ignition-progress-fill {
  height: 100%;
  border-radius: inherit;
  background:
    linear-gradient(90deg, #7dffbd, #ffd057, #ffffff);
  box-shadow:
    0 0 24px rgba(125, 255, 189, 0.42),
    0 0 34px rgba(255, 208, 87, 0.22);
  transition: width 80ms linear;
}

.ignition-progress-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  color: rgba(255,255,255,0.56);
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.ignition-readouts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 28px;
}

.ignition-readouts div {
  padding: 14px;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 18px;
  background: rgba(0,0,0,0.34);
}

.ignition-readouts span,
.ignition-readouts strong {
  display: block;
}

.ignition-readouts span {
  color: rgba(255,255,255,0.46);
  font-size: 0.66rem;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.ignition-readouts strong {
  margin-top: 7px;
  color: rgba(255,255,255,0.94);
  font-size: 0.82rem;
  font-weight: 950;
}

@keyframes ignitionRoad {
  from {
    transform: perspective(700px) rotateX(62deg) translateY(25%) translateX(0);
  }

  to {
    transform: perspective(700px) rotateX(62deg) translateY(25%) translateX(82px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .ignition-speed-lines {
    animation: none;
  }
}

@media (max-width: 700px) {
  .ignition-panel {
    padding: 22px;
    border-radius: 24px;
  }

  .ignition-readouts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .ignition-copy h1 {
    font-size: clamp(1.8rem, 12vw, 3.5rem);
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

    if "function WolfIgnitionSequence" not in text:
        marker = "function App() {"

        if marker not in text:
            raise RuntimeError("Could not find function App() marker.")

        text = text.replace(
            marker,
            IGNITION_COMPONENT + marker,
            1,
        )

        print("Added WolfIgnitionSequence component.")
    else:
        print("Ignition component already exists.")

    if "const [showIgnition" not in text:
        marker = "function App() {"

        text = text.replace(
            marker,
            marker + "\n" + IGNITION_STATE,
            1,
        )

        print("Added ignition state.")
    else:
        print("Ignition state already exists.")

    if "<WolfIgnitionSequence" not in text:
        marker = '<main className="v3-app">'

        if marker not in text:
            raise RuntimeError("Could not find v3-app main element.")

        text = text.replace(
            marker,
            marker + "\n" + IGNITION_RENDER,
            1,
        )

        print("Added ignition render overlay.")
    else:
        print("Ignition overlay already rendered.")

    APP_PATH.write_text(text, encoding="utf-8")


def patch_css() -> None:
    text = CSS_PATH.read_text(encoding="utf-8")

    if "WOLF OS 3.1-second ignition sequence" in text:
        print("Ignition CSS already exists.")
        return

    CSS_PATH.write_text(
        text.rstrip() + "\n" + IGNITION_CSS + "\n",
        encoding="utf-8",
    )

    print("Added ignition CSS.")


def run_build() -> None:
    print("\nRunning frontend build...")

    result = subprocess.run(
        ["npm", "run", "build"],
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

    print("WOLF OS ignition patch starting...")

    backup_file(APP_PATH, "ignition")
    backup_file(CSS_PATH, "ignition")

    patch_app()
    patch_css()
    run_build()

    print("\nIgnition sequence installed successfully.")
    print(r"Start locally with:")
    print(r"cd X:\i-am-the-one-saas")
    print(r".\start-local.ps1")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)