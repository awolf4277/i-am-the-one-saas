// Copyright © 2026 Andrew Wolverton. All Rights Reserved.
// I AM THE ONE™ · WOLF OS™ Theft Lock v1

const OWNER = "Andrew Wolverton";
const BRAND = "I AM THE ONE™";
const SYSTEM = "WOLF OS™";
const YEAR = "2026";
const EMAIL = "awolf4277@gmail.com";

function injectTheftLockBadge() {
  if (typeof document === "undefined") return;
  if (document.getElementById("wolf-os-theft-lock")) return;

  const style = document.createElement("style");
  style.setAttribute("data-wolf-os", "theft-lock");
  style.textContent = `
    #wolf-os-theft-lock {
      position: fixed;
      right: 14px;
      bottom: 14px;
      z-index: 99999;
      max-width: min(390px, calc(100vw - 28px));
      padding: 10px 14px;
      border: 1px solid rgba(94, 234, 212, 0.35);
      border-radius: 999px;
      background: rgba(2, 6, 23, 0.86);
      color: rgba(226, 232, 240, 0.94);
      font: 800 11px/1.25 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      box-shadow: 0 18px 60px rgba(0, 0, 0, 0.38), 0 0 28px rgba(94, 234, 212, 0.12);
      backdrop-filter: blur(16px);
      user-select: none;
      pointer-events: none;
    }

    #wolf-os-theft-lock span {
      color: #5eead4;
    }

    @media (max-width: 700px) {
      #wolf-os-theft-lock {
        left: 12px;
        right: 12px;
        bottom: 10px;
        text-align: center;
        border-radius: 18px;
      }
    }
  `;

  const badge = document.createElement("div");
  badge.id = "wolf-os-theft-lock";
  badge.setAttribute("aria-hidden", "true");
  badge.innerHTML = `<span>Protected:</span> ${BRAND} · ${SYSTEM} · © ${YEAR} ${OWNER}`;

  document.head.appendChild(style);
  document.body.appendChild(badge);
}

function printOwnershipWarning() {
  if (typeof console === "undefined") return;

  const title = `${BRAND} · ${SYSTEM}`;
  const body =
    `\nPROPRIETARY SOFTWARE NOTICE\n` +
    `Copyright © ${YEAR} ${OWNER}. All Rights Reserved.\n\n` +
    `This demo, source code, UI, branding, workflows, and backend architecture are proprietary.\n` +
    `Viewing frontend assets in a browser does not grant permission to copy, clone, resell, redistribute, or reuse this system.\n\n` +
    `Owner: ${OWNER}\n` +
    `Contact: ${EMAIL}\n`;

  console.log(
    `%c${title}%c${body}`,
    "background:#020617;color:#5eead4;font-size:18px;font-weight:900;padding:8px 10px;border-radius:8px;",
    "color:#e2e8f0;font-size:12px;line-height:1.5;"
  );
}

export function activateTheftLock() {
  printOwnershipWarning();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectTheftLockBadge, { once: true });
  } else {
    injectTheftLockBadge();
  }
}

activateTheftLock();
