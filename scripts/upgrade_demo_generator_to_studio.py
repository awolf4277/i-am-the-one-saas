from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
APP_PATH = FRONTEND_ROOT / "src" / "App.tsx"
CSS_PATH = FRONTEND_ROOT / "src" / "styles.css"


NEW_COMPONENT = r'''
function BusinessDemoGenerator() {
  const [industry, setIndustry] = useState<DemoIndustry>("barber");
  const [businessName, setBusinessName] = useState("Wolf Cuts");
  const [brandTone, setBrandTone] = useState("Premium");
  const [accentColor, setAccentColor] = useState("#7dffbd");
  const [logoUrl, setLogoUrl] = useState("");

  const [generatedName, setGeneratedName] = useState("Wolf Cuts");
  const [generatedIndustry, setGeneratedIndustry] =
    useState<DemoIndustry>("barber");
  const [generatedTone, setGeneratedTone] = useState("Premium");
  const [generatedColor, setGeneratedColor] = useState("#7dffbd");
  const [generatedLogo, setGeneratedLogo] = useState("");

  const [copied, setCopied] = useState(false);
  const [generationPulse, setGenerationPulse] = useState(0);

  const preset = DEMO_PRESETS[generatedIndustry];

  const generateDemo = () => {
    const cleanName =
      businessName.trim() || DEMO_PRESETS[industry].label;

    setGeneratedName(cleanName);
    setGeneratedIndustry(industry);
    setGeneratedTone(brandTone);
    setGeneratedColor(accentColor);
    setGeneratedLogo(logoUrl.trim());
    setCopied(false);
    setGenerationPulse((current) => current + 1);
  };

  const demoPitch = `${generatedName} Demo Direction

Industry:
${preset.label}

Brand Tone:
${generatedTone}

Headline:
${preset.headline}

Target Customer:
${preset.audience}

Recommended Package:
${preset.packageName} — ${preset.packagePrice}

Suggested Offers:
${preset.offers.map((offer) => `- ${offer}`).join("\n")}

Owner Dashboard Focus:
${preset.dashboardLabel}

Build Direction:
A ${generatedTone.toLowerCase()} buyer-ready storefront, lead or checkout flow, owner dashboard, live offers, and launch-ready structure customized for ${generatedName}.`;

  const copyDemoPitch = async () => {
    await navigator.clipboard.writeText(demoPitch);
    setCopied(true);

    window.setTimeout(() => {
      setCopied(false);
    }, 1600);
  };

  const demoStyle = {
    "--demo-accent": generatedColor,
    "--demo-accent-soft": `${generatedColor}22`,
    "--demo-accent-border": `${generatedColor}55`
  } as React.CSSProperties;

  return (
    <section
      className="business-demo-generator demo-studio"
      style={demoStyle}
    >
      <div className="demo-generator-head">
        <div>
          <p className="demo-generator-kicker">
            WOLF OS™ DEMO STUDIO
          </p>

          <h2>
            Build a personalized business demo in seconds.
          </h2>

          <p>
            Enter a business name, choose an industry, set the tone,
            pick an accent color, and generate a tailored storefront
            concept with offers, dashboard focus, and package direction.
          </p>
        </div>

        <div className="demo-generator-badge">
          <span>DEMO ENGINE</span>
          <strong>STUDIO</strong>
          <small>Personalization active</small>
        </div>
      </div>

      <div className="demo-generator-layout">
        <div className="demo-generator-controls">
          <label>
            Business name
            <input
              value={businessName}
              onChange={(event) =>
                setBusinessName(event.target.value)
              }
              placeholder="Enter business name"
            />
          </label>

          <label>
            Industry
            <select
              value={industry}
              onChange={(event) =>
                setIndustry(
                  event.target.value as DemoIndustry
                )
              }
            >
              <option value="barber">Barbershop</option>
              <option value="clothing">Clothing Brand</option>
              <option value="pressure-washing">
                Pressure Washing
              </option>
              <option value="food-truck">Food Truck</option>
              <option value="auto-detailing">
                Auto Detailing
              </option>
              <option value="landscaping">
                Landscaping
              </option>
            </select>
          </label>

          <label>
            Brand tone
            <select
              value={brandTone}
              onChange={(event) =>
                setBrandTone(event.target.value)
              }
            >
              <option value="Premium">Premium</option>
              <option value="Bold">Bold</option>
              <option value="Modern">Modern</option>
              <option value="Clean">Clean</option>
              <option value="Luxury">Luxury</option>
              <option value="Aggressive">Aggressive</option>
            </select>
          </label>

          <label>
            Accent color
            <div className="demo-color-control">
              <input
                type="color"
                value={accentColor}
                onChange={(event) =>
                  setAccentColor(event.target.value)
                }
              />

              <input
                value={accentColor}
                onChange={(event) =>
                  setAccentColor(event.target.value)
                }
                placeholder="#7dffbd"
              />
            </div>
          </label>

          <label>
            Logo image URL
            <input
              value={logoUrl}
              onChange={(event) =>
                setLogoUrl(event.target.value)
              }
              placeholder="Optional logo URL"
            />
          </label>

          <button
            type="button"
            className="v3-button primary full"
            onClick={generateDemo}
          >
            Generate Personalized Demo
          </button>

          <button
            type="button"
            className="v3-button secondary full"
            onClick={copyDemoPitch}
          >
            {copied ? "Demo Pitch Copied" : "Copy Demo Pitch"}
          </button>
        </div>

        <div
          className="generated-demo-preview demo-studio-preview"
          key={generationPulse}
        >
          <div className="generated-demo-toolbar">
            <span className="generated-demo-status">
              <i />
              DEMO GENERATED
            </span>

            <span>
              {preset.label} · {generatedTone}
            </span>
          </div>

          <div className="generated-demo-hero">
            <div className="demo-brand-row">
              {generatedLogo ? (
                <img
                  src={generatedLogo}
                  alt={`${generatedName} logo`}
                  className="generated-demo-logo"
                />
              ) : (
                <div className="generated-demo-logo-fallback">
                  {generatedName
                    .slice(0, 2)
                    .toUpperCase()}
                </div>
              )}

              <div>
                <p>
                  {preset.label.toUpperCase()} · WOLF OS™ POWERED
                </p>
                <h3>{generatedName}</h3>
              </div>
            </div>

            <strong>{preset.headline}</strong>
            <span>{preset.audience}</span>

            <div className="generated-demo-actions">
              <button type="button">
                View Offers
              </button>

              <button type="button">
                Request Setup
              </button>
            </div>
          </div>

          <div className="generated-offer-grid">
            {preset.offers.map((offer, index) => (
              <article key={offer}>
                <small>
                  OFFER {String(index + 1).padStart(2, "0")}
                </small>

                <strong>{offer}</strong>
                <span>{generatedTone} buyer-ready package</span>
              </article>
            ))}
          </div>

          <div className="generated-dashboard-preview">
            <div>
              <small>RECOMMENDED PACKAGE</small>
              <strong>{preset.packageName}</strong>
              <span>{preset.packagePrice}</span>
            </div>

            <div>
              <small>OWNER DASHBOARD</small>
              <strong>{preset.dashboardLabel}</strong>
              <span>Live control center</span>
            </div>

            <div>
              <small>BRAND MODE</small>
              <strong>{generatedTone.toUpperCase()}</strong>
              <span>{generatedColor}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
'''


EXTRA_CSS = r'''

/* WOLF OS Demo Studio upgrade */
.demo-studio {
  --demo-accent: #7dffbd;
  --demo-accent-soft: rgba(125, 255, 189, 0.12);
  --demo-accent-border: rgba(125, 255, 189, 0.34);
}

.demo-studio .demo-generator-kicker,
.demo-studio .demo-generator-badge strong,
.demo-studio .generated-demo-status,
.demo-studio .generated-dashboard-preview strong {
  color: var(--demo-accent);
}

.demo-studio .demo-generator-badge,
.demo-studio .generated-demo-hero,
.demo-studio .generated-dashboard-preview > div {
  border-color: var(--demo-accent-border);
}

.demo-studio .generated-demo-hero {
  background:
    radial-gradient(
      circle at top left,
      var(--demo-accent-soft),
      transparent 48%
    ),
    rgba(0, 0, 0, 0.38);
}

.demo-studio .generated-demo-status i {
  background: var(--demo-accent);
  box-shadow: 0 0 20px var(--demo-accent);
}

.demo-color-control {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 10px;
}

.demo-color-control input[type="color"] {
  height: 46px;
  padding: 4px;
  cursor: pointer;
}

.demo-brand-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.generated-demo-logo,
.generated-demo-logo-fallback {
  width: 72px;
  height: 72px;
  flex: 0 0 auto;
  border: 1px solid var(--demo-accent-border);
  border-radius: 20px;
  background: rgba(0, 0, 0, 0.42);
  box-shadow:
    0 0 28px var(--demo-accent-soft),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.generated-demo-logo {
  object-fit: cover;
}

.generated-demo-logo-fallback {
  display: grid;
  place-items: center;
  color: var(--demo-accent);
  font-size: 1.4rem;
  font-weight: 950;
  letter-spacing: -0.06em;
}

.generated-demo-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.generated-demo-actions button {
  padding: 10px 14px;
  border: 1px solid var(--demo-accent-border);
  border-radius: 999px;
  background: var(--demo-accent-soft);
  color: rgba(255, 255, 255, 0.92);
  font-weight: 850;
  cursor: pointer;
}

.demo-studio-preview {
  animation: demoStudioIgnition 520ms ease;
}

@keyframes demoStudioIgnition {
  0% {
    opacity: 0.3;
    transform: translateY(12px) scale(0.985);
    filter: blur(4px);
  }

  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .demo-studio-preview {
    animation: none;
  }
}

@media (max-width: 560px) {
  .demo-brand-row {
    align-items: flex-start;
  }

  .generated-demo-logo,
  .generated-demo-logo-fallback {
    width: 58px;
    height: 58px;
    border-radius: 16px;
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


def replace_component() -> None:
    text = APP_PATH.read_text(encoding="utf-8")

    start_marker = "function BusinessDemoGenerator() {"
    end_marker = "\n\nfunction CustomerStorefront({"

    start = text.find(start_marker)
    end = text.find(end_marker, start)

    if start == -1:
        raise RuntimeError(
            "BusinessDemoGenerator component was not found."
        )

    if end == -1:
        raise RuntimeError(
            "Could not find the end of BusinessDemoGenerator."
        )

    updated = (
        text[:start]
        + NEW_COMPONENT
        + text[end:]
    )

    APP_PATH.write_text(updated, encoding="utf-8")
    print("Upgraded Business Demo Generator to Demo Studio.")


def patch_css() -> None:
    text = CSS_PATH.read_text(encoding="utf-8")

    if "WOLF OS Demo Studio upgrade" in text:
        print("Demo Studio CSS already exists.")
        return

    CSS_PATH.write_text(
        text.rstrip() + "\n" + EXTRA_CSS + "\n",
        encoding="utf-8",
    )

    print("Added Demo Studio CSS.")


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

    print("WOLF OS Demo Studio upgrade starting...")

    backup_file(APP_PATH, "demo-studio")
    backup_file(CSS_PATH, "demo-studio")

    replace_component()
    patch_css()
    run_build()

    print("\nDemo Studio upgrade installed successfully.")
    print(r"Start locally with:")
    print(r"cd X:\i-am-the-one-saas")
    print(r".\start-local.ps1")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)