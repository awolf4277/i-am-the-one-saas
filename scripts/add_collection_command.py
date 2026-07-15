from pathlib import Path
from datetime import datetime
import shutil
import subprocess

ROOT = Path(r"X:\i-am-the-one-saas")
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

BACKEND_APP = (
    BACKEND
    / "app"
    / "__init__.py"
)

APP = (
    FRONTEND
    / "src"
    / "App.tsx"
)

STYLES = (
    FRONTEND
    / "src"
    / "styles.css"
)

STAMP = datetime.now().strftime(
    "%Y%m%d-%H%M%S"
)

BACKUP_DIR = (
    ROOT
    / "backups"
    / "collection-command"
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
    "WOLF OS COLLECTION COMMAND patch starting..."
)

for path in [
    BACKEND_APP,
    APP,
    STYLES,
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


backend_text = BACKEND_APP.read_text(
    encoding="utf-8",
)

app_text = APP.read_text(
    encoding="utf-8",
)

styles_text = STYLES.read_text(
    encoding="utf-8",
)


# =================================================
# BACKEND PAYMENT STATUS ROUTE
# =================================================

payment_route_marker = (
    '/api/owner/orders/'
    '<order_id>/payment-status'
)

if payment_route_marker in backend_text:
    stop(
        "Collection Command payment route "
        "already exists."
    )

owner_products_anchor = '''    @app.route("/api/owner/products", methods=["GET", "POST"])
'''

payment_route = '''    @app.put("/api/owner/orders/<order_id>/payment-status")
    def owner_update_order_payment_status(
        order_id: str
    ):
        ok, error = require_owner()

        if not ok:
            return error

        payload = request.get_json(
            silent=True
        )

        if payload is None:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Request body must contain "
                        "valid JSON."
                    ),
                }
            ), 400

        if not isinstance(payload, dict):
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "Payment status payload must "
                        "be a JSON object."
                    ),
                }
            ), 400

        if "payment_status" not in payload:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "payment_status is required."
                    ),
                }
            ), 400

        payment_status = str(
            payload["payment_status"]
            or ""
        ).strip().lower()

        allowed_statuses = {
            "paid",
            "unpaid",
        }

        if payment_status not in allowed_statuses:
            return jsonify(
                {
                    "ok": False,
                    "error": (
                        "payment_status must be "
                        "paid or unpaid."
                    ),
                }
            ), 400

        con = connect(app)

        try:
            order = con.execute(
                """
                SELECT *
                FROM orders
                WHERE id = ?
                LIMIT 1
                """,
                (order_id,),
            ).fetchone()

            if not order:
                return jsonify(
                    {
                        "ok": False,
                        "error": "Order not found.",
                    }
                ), 404

            previous_status = str(
                order["payment_status"]
                or "unpaid"
            ).strip().lower()

            if previous_status != payment_status:
                con.execute(
                    """
                    UPDATE orders
                    SET payment_status = ?
                    WHERE id = ?
                    """,
                    (
                        payment_status,
                        order_id,
                    ),
                )

                con.commit()

            updated_order = con.execute(
                """
                SELECT *
                FROM orders
                WHERE id = ?
                LIMIT 1
                """,
                (order_id,),
            ).fetchone()

            return jsonify(
                {
                    "ok": True,
                    "changed": (
                        previous_status
                        != payment_status
                    ),
                    "previous_payment_status": (
                        previous_status
                    ),
                    "payment_status": (
                        payment_status
                    ),
                    "order": dict(
                        updated_order
                    ),
                }
            )

        finally:
            con.close()


'''

backend_text = replace_once(
    backend_text,
    owner_products_anchor,
    payment_route + owner_products_anchor,
    "owner payment status PUT route",
)


# =================================================
# FRONTEND PAYMENT UPDATE HANDLER
# =================================================

handler_anchor = '''  async function createOwnerProduct(form: ProductForm) {
'''

payment_handler = '''  async function updateOrderPaymentStatus(
    orderId: string,
    paymentStatus: "paid" | "unpaid"
  ) {
    if (!ownerToken) {
      setError(
        "Owner token required."
      );
      return;
    }

    try {
      setError("");

      const payload =
        await apiJson<any>(
          `/api/owner/orders/${
            encodeURIComponent(
              orderId
            )
          }/payment-status`,
          {
            method: "PUT",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              payment_status:
                paymentStatus,
            }),
          },
          ownerToken
        );

      if (!payload?.ok) {
        throw new Error(
          payload?.error ||
            "Payment status update failed."
        );
      }

      setNotice(
        paymentStatus === "paid"
          ? `PAYMENT CAPTURED · ${orderId}`
          : `PAYMENT REOPENED · ${orderId}`
      );

      await loadOwnerData(
        ownerToken
      );
    } catch (err: any) {
      setError(
        err?.message ||
          "Payment status update failed."
      );
    }
  }

'''

app_text = replace_once(
    app_text,
    handler_anchor,
    payment_handler + handler_anchor,
    "Collection Command payment handler",
)


# =================================================
# REAL ORDERS PAYMENT CONTROL
# =================================================

old_payment_status = '''                  <span>{order.payment_status || order.status || "pending"}</span>
'''

new_payment_control = '''                  <div className="owner-payment-command">
                    <span
                      className={`owner-payment-status ${
                        String(
                          order.payment_status ||
                            "unpaid"
                        )
                          .trim()
                          .toLowerCase() === "paid"
                          ? "paid"
                          : "unpaid"
                      }`}
                    >
                      {order.payment_status ||
                        order.status ||
                        "pending"}
                    </span>

                    {order.id ? (
                      <div className="owner-payment-actions">
                        {String(
                          order.payment_status ||
                            "unpaid"
                        )
                          .trim()
                          .toLowerCase() === "paid" ? (
                          <button
                            type="button"
                            className="owner-payment-button reopen"
                            onClick={() =>
                              updateOrderPaymentStatus(
                                order.id as string,
                                "unpaid"
                              )
                            }
                          >
                            MARK UNPAID
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="owner-payment-button collect"
                            onClick={() =>
                              updateOrderPaymentStatus(
                                order.id as string,
                                "paid"
                              )
                            }
                          >
                            MARK PAID
                          </button>
                        )}
                      </div>
                    ) : null}
                  </div>
'''

app_text = replace_once(
    app_text,
    old_payment_status,
    new_payment_control,
    "Real Orders Collection Command controls",
)


# =================================================
# COLLECTION COMMAND CSS
# =================================================

collection_css_marker = (
    "/* WOLF OS COLLECTION COMMAND */"
)

if collection_css_marker in styles_text:
    stop(
        "Collection Command CSS "
        "already exists."
    )

collection_css = '''

/* WOLF OS COLLECTION COMMAND */

.owner-payment-command {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.45rem;
}

.owner-payment-status {
  display: inline-flex;
  align-items: center;
  min-width: 4.7rem;
  justify-content: center;
  padding: 0.28rem 0.55rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.owner-payment-status.paid {
  border-color: rgba(70, 255, 164, 0.5);
  background: rgba(70, 255, 164, 0.1);
  box-shadow:
    0 0 18px rgba(70, 255, 164, 0.12);
}

.owner-payment-status.unpaid {
  border-color: rgba(255, 181, 71, 0.45);
  background: rgba(255, 181, 71, 0.08);
}

.owner-payment-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.owner-payment-button {
  appearance: none;
  border-radius: 0.55rem;
  padding: 0.45rem 0.62rem;
  font: inherit;
  font-size: 0.64rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  cursor: pointer;
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    border-color 160ms ease;
}

.owner-payment-button:hover {
  transform: translateY(-1px);
}

.owner-payment-button.collect {
  border: 1px solid rgba(70, 255, 164, 0.55);
  background: rgba(70, 255, 164, 0.12);
  box-shadow:
    0 0 18px rgba(70, 255, 164, 0.1);
}

.owner-payment-button.collect:hover {
  box-shadow:
    0 0 24px rgba(70, 255, 164, 0.2);
}

.owner-payment-button.reopen {
  border: 1px solid rgba(255, 181, 71, 0.48);
  background: rgba(255, 181, 71, 0.1);
}

.owner-payment-button.reopen:hover {
  box-shadow:
    0 0 22px rgba(255, 181, 71, 0.16);
}
'''

styles_text += collection_css

print(
    "Patched: Collection Command CSS"
)


# =================================================
# SAFETY CHECKS BEFORE WRITE
# =================================================

if payment_route_marker not in backend_text:
    stop(
        "Backend payment route missing "
        "after patch."
    )

if (
    "async function updateOrderPaymentStatus"
    not in app_text
):
    stop(
        "Frontend payment handler missing "
        "after patch."
    )

if "MARK PAID" not in app_text:
    stop(
        "MARK PAID control missing."
    )

if "MARK UNPAID" not in app_text:
    stop(
        "MARK UNPAID control missing."
    )

if (
    collection_css_marker
    not in styles_text
):
    stop(
        "Collection Command CSS marker missing."
    )


# =================================================
# WRITE PATCHED FILES
# =================================================

BACKEND_APP.write_text(
    backend_text,
    encoding="utf-8",
)

APP.write_text(
    app_text,
    encoding="utf-8",
)

STYLES.write_text(
    styles_text,
    encoding="utf-8",
)

print(
    "Collection Command source files written."
)


# =================================================
# VERIFY BACKEND ROUTE
# =================================================

print()
print(
    "--- VERIFYING COLLECTION API ROUTE ---"
)

python = (
    BACKEND
    / ".venv"
    / "Scripts"
    / "python.exe"
)

backend_result = subprocess.run(
    [
        str(python),
        "-c",
        (
            "import wsgi; "
            "routes={"
            "str(rule): sorted(rule.methods) "
            "for rule in "
            "wsgi.app.url_map.iter_rules()"
            "}; "
            "route='/api/owner/orders/"
            "<order_id>/payment-status'; "
            "assert route in routes; "
            "assert 'PUT' in routes[route]; "
            "print("
            "'COLLECTION API ROUTE OK', "
            "routes[route]"
            ")"
        ),
    ],
    cwd=BACKEND,
    text=True,
)

if backend_result.returncode != 0:
    stop(
        "Collection API route verification "
        "failed."
    )


# =================================================
# FRONTEND PRODUCTION BUILD
# =================================================

print()
print(
    "--- RUNNING FRONTEND BUILD ---"
)

frontend_result = subprocess.run(
    [
        "npm.cmd",
        "run",
        "build",
    ],
    cwd=FRONTEND,
    text=True,
)

if frontend_result.returncode != 0:
    stop(
        "Frontend build failed. "
        "Review the TypeScript error above."
    )


print()
print(
    "SUCCESS: WOLF OS COLLECTION COMMAND INSTALLED."
)

print(
    "MARK PAID and MARK UNPAID now write "
    "real SQLite payment status."
)

print(
    "Revenue Truth will recalculate after "
    "the owner order reload."
)