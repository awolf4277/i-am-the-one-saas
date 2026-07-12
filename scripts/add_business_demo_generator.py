from pathlib import Path
from datetime import datetime
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(r"X:\i-am-the-one-saas")
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
APP_PATH = FRONTEND_ROOT / "src" / "App.tsx"
CSS_PATH = FRONTEND_ROOT / "src" / "styles.css"


DEMO_GENERATOR_COMPONENT = r'''

type DemoIndustry =
  | "barber"
  | "clothing"
  | "pressure-washing"
  | "food-truck"
  | "auto-detailing"
  | "landscaping";

type DemoPreset = {
  label: string;
  headline: string;
  audience: string;
  packageName: string;
  packagePrice: string;
  dashboardLabel: string;
  offers: string[];
};

const DEMO_PRESETS: Record<DemoIndustry, DemoPreset> = {
  barber: {
    label: "Barbershop",
    headline: "Turn appointments and grooming packages into a premium local buying experience.",
    audience: "Local customers looking for haircuts, beard services, and recurring grooming.",
    packageName: "Pro Storefront + Booking Dashboard",
    packagePrice: "$1,500+",
    dashboardLabel: "Appointments",
    offers: [
      "Signature Haircut — $35",
      "Haircut + Beard Package — $55",
      "VIP Grooming Experience — $85"
    ]
  },

  clothing: {
    label: "Clothing Brand",
    headline: "Launch a bold storefront for products, drops, bundles, and branded merchandise.",
    audience: "Style-focused customers who want premium apparel and limited releases.",
    packageName: "Pro Storefront + Inventory Dashboard",
    packagePrice: "$1,500+",
    dashboardLabel: "Inventory",
    offers: [
      "Premium Hoodie — $89",
      "Signature Tee — $39",
      "Launch Bundle — $149"
    ]
  },

  "pressure-washing": {
    label: "Pressure Washing",
    headline: "Capture local service leads and sell exterior-cleaning packages online.",
    audience: "Homeowners and property managers who need reliable exterior cleaning.",
    packageName: "Starter Service Storefront",
    packagePrice: "$499+",
    dashboardLabel: "Service Leads",
    offers: [
      "Driveway Cleaning — $149",
      "House Wash — $299",
      "Full Exterior Package — $499"
    ]
  },

  "food-truck": {
    label: "Food Truck",
    headline: "Showcase menu items, catering packages, locations, and event requests.",
    audience: "Local customers, event organizers, offices, and catering buyers.",
    packageName: "Pro Menu + Catering Dashboard",
    packagePrice: "$1,500+",
    dashboardLabel: "Catering Requests",
    offers: [
      "Signature Meal — $15",
      "Family Pack — $59",
      "Event Catering Deposit — $250"
    ]
  },

  "auto-detailing": {
    label: "Auto Detailing",
    headline: "Sell detailing packages and turn vehicle-care interest into booked work.",
    audience: "Vehicle owners who want professional interior and exterior detailing.",
    packageName: "Pro Service Storefront + Dashboard",
    packagePrice: "$1,500+",
    dashboardLabel: "Service Orders",
    offers: [
      "Interior Detail — $175",
      "Full Detail — $299",
      "Ceramic Package — $799"
    ]
  },

  landscaping: {
    label: "Landscaping",
    headline: "Present outdoor-service packages and capture quote-ready local buyers.",
    audience: "Homeowners and businesses looking for lawn, landscape, and seasonal services.",
    packageName: "Starter Service Storefront",
    packagePrice: "$499+",
    dashboardLabel: "Quote Leads",
    offers: [
      "Lawn Care Plan — $149",
      "Landscape Cleanup — $399",
      "Property Upgrade Package — $1,200"
    ]
  }
};

function BusinessDemoGenerator() {
  const [industry, setIndustry] = useState<DemoIndustry>("barber");
  const [businessName, setBusinessName] = useState("Wolf Cuts");
  const [generatedName, setGeneratedName] = useState("Wolf Cuts");
  const [generatedIndustry, setGeneratedIndustry] = useState<DemoIndustry>("barber");
  const [copied, setCopied] = useState(false);

  const preset = DEMO_PRESETS[generatedIndustry];

  const generateDemo = () => {
    const cleanName = businessName.trim() || DEMO_PRESETS[industry].label;

    setGeneratedName(cleanName);
    setGeneratedIndustry(industry);
    setCopied(false);
  };

  const demoPitch = `${generatedName} Demo Direction

Industry:
${preset.label}

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
A buyer-ready storefront, lead or checkout flow, owner dashboard, live offers, and launch-ready structure customized for ${generatedName}.`;

  const copyDemoPitch = async () => {
    await navigator.clipboard.writeText(demoPitch);
    setCopied(true);

    window.setTimeout(() => {
      setCopied(false);
    }, 1600);
  };

  return (
    <section className="business-demo-generator">
      <div className="demo-generator-head">
        <div>
          <p className="demo-generator-kicker">WOLF OS™ BUSINESS DEMO GENERATOR</p>
          <h2>Turn a business idea into a buyer-ready demo direction.</h2>
          <p>
            Choose an industry, enter a business name, and generate a tailored
            storefront concept, offer list, dashboard focus, and recommended package.
          </p>
        </div>

        <div className="demo-generator-badge">
          <span>DEMO ENGINE</span>
          <strong>READY</strong>
          <small>Six business modes loaded</small>
        </div>
      </div>

      <div className="demo-generator-layout">
        <div className="demo-generator-controls">
          <label>
            Business name
            <input
              value={businessName}
              onChange={(event) => setBusinessName(event.target.value)}
              placeholder="Enter business name"
            />
          </label>

          <label>
            Industry
            <select
              value={industry}
              onChange={(event) => setIndustry(event.target.value as DemoIndustry)}
            >
              <option value="barber">Barbershop</option>
              <option value="clothing">Clothing Brand</option>
              <option value="pressure-washing">Pressure Washing</option>
              <option value="food-truck">Food Truck</option>
              <option value="auto-detailing">Auto Detailing</option>
              <option value="landscaping">Landscaping</option>
            </select>
          </label>

          <button
            type="button"
            className="v3-button primary full"
            onClick={generateDemo}
          >
            Generate Business Demo
          </button>

          <button
            type="button"
            className="v3-button secondary full"
            onClick={copyDemoPitch}
          >
            {copied ? "Demo Pitch Copied" : "Copy Demo Pitch"}
          </button>
        </div>

        <div className="generated-demo-preview">
          <div className="generated-demo-toolbar">
            <span className="generated-demo-status">
              <i />
              DEMO GENERATED
            </span>

            <span>{preset.label}</span>
          </div>

          <div className="generated-demo-hero">
            <p>{preset.label.toUpperCase()} · WOLF OS™ POWERED</p>
            <h3>{generatedName}</h3>
            <strong>{preset.headline}</strong>
            <span>{preset.audience}</span>
          </div>

          <div className="generated-offer-grid">
            {preset.offers.map((offer, index) => (
              <article key={offer}>
                <small>OFFER {String(index + 1).padStart(2, "0")}</small>
                <strong>{offer}</strong>
                <span>Buyer-ready package</span>
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
              <small>LAUNCH MODE</small>
              <strong>BUYER READY</strong>
              <span>Storefront + owner workflow</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

'''


DEMO_GENERATOR_INSERT = r'''
      <div className="landing-cockpit-span">
        <BusinessDemoGenerator />
      </div>

'''


DEMO_GENERATOR_CSS = r'''

/* WOLF OS Business Demo Generator */
.business-demo-generator {
  grid-column: 1 / -1;
  margin: 0 0 12px;
  padding: 28px;
  border: 1px solid rgba(125, 255, 189, 0.2);
  border-radius: 30px;
  background:
    radial-gradient(circle at 8% 0%, rgba(125, 255, 189, 0.16), transparent 35%),
    radial-gradient(circle at 92% 10%, rgba(145, 211, 255, 0.12), transparent 32%),
    linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02)),
    rgba(2, 5, 8, 0.93);
  box-shadow:
    0 34px 110px rgba(0, 0, 0, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.business-demo-generator::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255,255,255,0.024) 1px, transparent 1px),
    linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: radial-gradient(circle at center, black, transparent 82%);
  pointer-events: none;
}

.demo-generator-head {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 24px;
  align-items: start;
}

.demo-generator-kicker {
  margin: 0 0 8px;
  color: #7dffbd;
  font-size: 0.76rem;
  font-weight: 950;
  letter-spacing: 0.2em;
}

.demo-generator-head h2 {
  margin: 0 0 10px;
  max-width: 840px;
  font-size: clamp(1.65rem, 3vw, 2.65rem);
  letter-spacing: -0.055em;
}

.demo-generator-head p {
  max-width: 800px;
  color: rgba(255,255,255,0.7);
}

.demo-generator-badge {
  min-width: 180px;
  padding: 18px;
  border: 1px solid rgba(125,255,189,0.22);
  border-radius: 24px;
  background: rgba(0,0,0,0.4);
  text-align: center;
}

.demo-generator-badge span,
.demo-generator-badge small {
  display: block;
  color: rgba(255,255,255,0.5);
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.demo-generator-badge strong {
  display: block;
  margin: 8px 0;
  color: #7dffbd;
  font-size: 1.7rem;
  letter-spacing: -0.05em;
  text-shadow: 0 0 22px rgba(125,255,189,0.3);
}

.demo-generator-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(260px, 0.6fr) minmax(0, 1.4fr);
  gap: 16px;
  margin-top: 24px;
}

.demo-generator-controls,
.generated-demo-preview {
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 24px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018)),
    rgba(0,0,0,0.36);
}

.demo-generator-controls {
  display: grid;
  align-content: start;
  gap: 15px;
  padding: 20px;
}

.demo-generator-controls label {
  display: grid;
  gap: 8px;
  color: rgba(255,255,255,0.64);
  font-size: 0.75rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.demo-generator-controls input,
.demo-generator-controls select {
  width: 100%;
  padding: 13px 14px;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px;
  background: rgba(0,0,0,0.4);
  color: rgba(255,255,255,0.95);
  font: inherit;
  text-transform: none;
  letter-spacing: normal;
}

.generated-demo-preview {
  padding: 18px;
  overflow: hidden;
}

.generated-demo-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding-bottom: 14px;
  color: rgba(255,255,255,0.52);
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.generated-demo-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #7dffbd;
}

.generated-demo-status i {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #7dffbd;
  box-shadow: 0 0 18px rgba(125,255,189,0.55);
}

.generated-demo-hero {
  padding: 24px;
  border: 1px solid rgba(125,255,189,0.15);
  border-radius: 20px;
  background:
    radial-gradient(circle at top left, rgba(125,255,189,0.12), transparent 42%),
    rgba(0,0,0,0.35);
}

.generated-demo-hero p {
  margin: 0 0 8px;
  color: #7dffbd;
  font-size: 0.68rem;
  font-weight: 950;
  letter-spacing: 0.16em;
}

.generated-demo-hero h3 {
  margin: 0;
  font-size: clamp(2rem, 5vw, 4rem);
  line-height: 0.95;
  letter-spacing: -0.075em;
}

.generated-demo-hero strong,
.generated-demo-hero span {
  display: block;
  max-width: 780px;
}

.generated-demo-hero strong {
  margin-top: 16px;
  color: rgba(255,255,255,0.92);
  font-size: 1.1rem;
}

.generated-demo-hero span {
  margin-top: 8px;
  color: rgba(255,255,255,0.56);
  line-height: 1.5;
}

.generated-offer-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 10px;
  margin-top: 12px;
}

.generated-offer-grid article {
  min-height: 130px;
  padding: 15px;
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 17px;
  background: rgba(0,0,0,0.3);
}

.generated-offer-grid small,
.generated-offer-grid strong,
.generated-offer-grid span {
  display: block;
}

.generated-offer-grid small {
  color: rgba(255,255,255,0.4);
  font-size: 0.65rem;
  font-weight: 900;
  letter-spacing: 0.1em;
}

.generated-offer-grid strong {
  margin: 13px 0 8px;
  color: rgba(255,255,255,0.94);
}

.generated-offer-grid span {
  color: rgba(255,255,255,0.48);
  font-size: 0.76rem;
}

.generated-dashboard-preview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0,1fr));
  gap: 10px;
  margin-top: 12px;
}

.generated-dashboard-preview > div {
  padding: 15px;
  border: 1px solid rgba(125,255,189,0.12);
  border-radius: 17px;
  background: rgba(125,255,189,0.035);
}

.generated-dashboard-preview small,
.generated-dashboard-preview strong,
.generated-dashboard-preview span {
  display: block;
}

.generated-dashboard-preview small {
  color: rgba(255,255,255,0.42);
  font-size: 0.64rem;
  font-weight: 900;
  letter-spacing: 0.1em;
}

.generated-dashboard-preview strong {
  margin: 10px 0 6px;
  color: #7dffbd;
}

.generated-dashboard-preview span {
  color: rgba(255,255,255,0.5);
  font-size: 0.74rem;
}

@media (max-width: 950px) {
  .demo-generator-head,
  .demo-generator-layout {
    grid-template-columns: 1fr;
  }

  .demo-generator-badge {
    width: 100%;
  }
}

@media (max-width: 720px) {
  .business-demo-generator {
    padding: 20px;
    border-radius: 24px;
  }

  .generated-offer-grid,
  .generated-dashboard-preview {
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

    if "function BusinessDemoGenerator" not in text:
        marker = "function CustomerStorefront({"

        if marker not in text:
            raise RuntimeError("Could not find CustomerStorefront marker.")

        text = text.replace(
            marker,
            DEMO_GENERATOR_COMPONENT + marker,
            1,
        )

        print("Added Business Demo Generator component.")
    else:
        print("Business Demo Generator component already exists.")

    if "<BusinessDemoGenerator />" not in text:
        landing_marker = '<section className="landing-grid">'

        if landing_marker not in text:
            raise RuntimeError("Could not find landing-grid marker.")

        text = text.replace(
            landing_marker,
            landing_marker + "\n" + DEMO_GENERATOR_INSERT,
            1,
        )

        print("Inserted Business Demo Generator into landing page.")
    else:
        print("Business Demo Generator already rendered.")

    APP_PATH.write_text(text, encoding="utf-8")


def patch_css() -> None:
    text = CSS_PATH.read_text(encoding="utf-8")

    if "WOLF OS Business Demo Generator" in text:
        print("Business Demo Generator CSS already exists.")
        return

    CSS_PATH.write_text(
        text.rstrip() + "\n" + DEMO_GENERATOR_CSS + "\n",
        encoding="utf-8",
    )

    print("Added Business Demo Generator CSS.")


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

    print("WOLF OS Business Demo Generator patch starting...")

    backup_file(APP_PATH, "business-demo-generator")
    backup_file(CSS_PATH, "business-demo-generator")

    patch_app()
    patch_css()
    run_build()

    print("\nBusiness Demo Generator installed successfully.")
    print(r"Start locally with:")
    print(r"cd X:\i-am-the-one-saas")
    print(r".\start-local.ps1")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)
