from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any


BASE = os.getenv(
    "WOLF_TEST_BASE_URL",
    "http://127.0.0.1:5000",
).rstrip("/")

MASTER_PASSWORD = os.getenv(
    "WOLF_LOCAL_OWNER_PASSWORD",
    "WOLF-DEMO",
)

STAMP = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

passed = 0
failed = 0


def call(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    token: str | None = None,
) -> tuple[int, Any]:

    headers = {
        "Accept": "application/json",
    }

    data = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=15,
        ) as response:

            raw = response.read().decode(
                "utf-8",
                errors="replace",
            )

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = raw

            return response.status, payload

    except urllib.error.HTTPError as exc:

        raw = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw

        return exc.code, payload


def check(
    name: str,
    condition: bool,
    detail: str = "",
) -> bool:

    global passed, failed

    if condition:
        passed += 1
        print(
            f"[PASS] {name}"
            + (f" -- {detail}" if detail else "")
        )
        return True

    failed += 1

    print(
        f"[FAIL] {name}"
        + (f" -- {detail}" if detail else "")
    )

    return False


def status_check(
    name: str,
    actual: int,
    expected: set[int],
) -> bool:

    return check(
        name,
        actual in expected,
        f"HTTP {actual}",
    )


def products_from(payload: Any) -> list[dict[str, Any]]:

    if isinstance(payload, list):
        return [
            x for x in payload
            if isinstance(x, dict)
        ]

    if isinstance(payload, dict):
        products = payload.get("products")

        if isinstance(products, list):
            return [
                x for x in products
                if isinstance(x, dict)
            ]

    return []


def orders_from(payload: Any) -> list[dict[str, Any]]:

    if isinstance(payload, dict):
        orders = payload.get("orders")

        if isinstance(orders, list):
            return [
                x for x in orders
                if isinstance(x, dict)
            ]

    return []


def payment_records_from(
    payload: Any,
) -> list[dict[str, Any]]:

    if not isinstance(payload, dict):
        return []

    records = payload.get("records")

    if not isinstance(records, list):
        records = payload.get("payment_records")

    if not isinstance(records, list):
        return []

    return [
        x for x in records
        if isinstance(x, dict)
    ]


def find_product(
    products: list[dict[str, Any]],
    sku: str,
) -> dict[str, Any] | None:

    wanted = sku.upper()

    for product in products:
        if str(
            product.get("sku") or ""
        ).upper() == wanted:
            return product

    return None


def find_order(
    orders: list[dict[str, Any]],
    order_id: str,
) -> dict[str, Any] | None:

    for order in orders:
        candidate = str(
            order.get("id")
            or order.get("order_id")
            or ""
        )

        if candidate == order_id:
            return order

    return None


def snapshot_products(
    products: list[dict[str, Any]],
) -> list[tuple[str, str, int, int]]:

    snapshot = []

    for product in products:

        snapshot.append(
            (
                str(product.get("id") or ""),
                str(product.get("sku") or ""),
                int(product.get("stock") or 0),
                int(product.get("price_cents") or 0),
            )
        )

    return sorted(snapshot)


print()
print("=" * 60)
print(" WOLF OS FULL TENANT REGRESSION")
print("=" * 60)
print(f"API: {BASE}")
print(f"RUN: {STAMP}")
print()


# ============================================================
# 1. HEALTH
# ============================================================

status, health = call(
    "GET",
    "/api/health",
)

status_check(
    "API health",
    status,
    {200},
)


# ============================================================
# 2. MASTER OWNER LOGIN
# ============================================================

status, login = call(
    "POST",
    "/api/owner/login",
    {
        "password": MASTER_PASSWORD,
    },
)

status_check(
    "Master owner login",
    status,
    {200},
)

master_token = ""

if isinstance(login, dict):
    master_token = str(
        login.get("token") or ""
    ).strip()

if not check(
    "Master owner token",
    bool(master_token),
):
    sys.exit(1)


# ============================================================
# 3. SNAPSHOT DEMO STORE
# ============================================================

status, demo_before_payload = call(
    "GET",
    "/api/stores/demo/products",
)

status_check(
    "Demo catalog before test",
    status,
    {200},
)

demo_before = snapshot_products(
    products_from(demo_before_payload)
)

check(
    "Demo catalog snapshot captured",
    len(demo_before) > 0,
    f"{len(demo_before)} products",
)


# ============================================================
# 4. CREATE TENANT A
# ============================================================

tenant_a_slug = f"wolf-qa-a-{STAMP}"
tenant_a_email = f"qa-a-{STAMP}@example.com"
tenant_a_password = f"WolfQA-A-{STAMP}!"

tenant_a_body = {
    "business_name": f"WOLF QA A {STAMP}",
    "store_slug": tenant_a_slug,
    "owner_name": "WOLF QA Owner A",
    "owner_email": tenant_a_email,
    "brand": "WOLF QA A",
    "system": "WOLF OS",
    "plan": "starter",
    "temporary_password": tenant_a_password,
}

status, tenant_a_created = call(
    "POST",
    "/api/owner/customer-accounts",
    tenant_a_body,
    master_token,
)

status_check(
    "Provision tenant A",
    status,
    {201},
)

tenant_a_account = {}

if isinstance(tenant_a_created, dict):
    tenant_a_account = (
        tenant_a_created.get(
            "customer_account"
        )
        or {}
    )

check(
    "Tenant A slug returned",
    str(
        tenant_a_account.get("store_slug")
        or ""
    ) == tenant_a_slug,
    tenant_a_slug,
)


# ============================================================
# 5. TENANT A LOGIN
# ============================================================

status, tenant_a_login = call(
    "POST",
    "/api/customer-owner/login",
    {
        "email": tenant_a_email,
        "password": tenant_a_password,
        "store_slug": tenant_a_slug,
    },
)

status_check(
    "Tenant A owner login",
    status,
    {200},
)

tenant_a_token = ""

if isinstance(tenant_a_login, dict):
    tenant_a_token = str(
        tenant_a_login.get("token") or ""
    ).strip()

if not check(
    "Tenant A token",
    bool(tenant_a_token),
):
    sys.exit(1)


status, _ = call(
    "GET",
    "/api/customer-owner/session",
    token=tenant_a_token,
)

status_check(
    "Tenant A session",
    status,
    {200},
)


# ============================================================
# 6. CREATE TENANT A PRODUCT
# ============================================================

sku = f"WOLF-QA-{STAMP}"
price_cents = 49900
starting_stock = 7

status, product_created = call(
    "POST",
    "/api/customer-owner/products",
    {
        "sku": sku,
        "name": "WOLF OS QA Product",
        "category": "Software",
        "description": (
            "Automated WOLF OS tenant regression product."
        ),
        "price_cents": price_cents,
        "stock": starting_stock,
        "image_url": "",
    },
    tenant_a_token,
)

status_check(
    "Create tenant A product",
    status,
    {200, 201},
)


# ============================================================
# 7. VERIFY PUBLIC TENANT PRODUCT
# ============================================================

status, catalog_a = call(
    "GET",
    f"/api/stores/{tenant_a_slug}/products",
)

status_check(
    "Tenant A public catalog",
    status,
    {200},
)

product_before = find_product(
    products_from(catalog_a),
    sku,
)

if not check(
    "Tenant A product visible publicly",
    product_before is not None,
    sku,
):
    sys.exit(1)

product_id = str(
    product_before.get("id") or ""
)

stock_before = int(
    product_before.get("stock") or 0
)

check(
    "Tenant A starting stock",
    stock_before == starting_stock,
    f"{stock_before}",
)


# ============================================================
# 8. CHECKOUT
# ============================================================

buyer_email = f"buyer-{STAMP}@example.com"

checkout_body = {
    "buyer": {
        "name": "WOLF QA Buyer",
        "email": buyer_email,
        "phone": "555-0100",
        "notes": "Automated Phase 2 regression checkout.",
    },
    "items": [
        {
            "product_id": product_id,
            "sku": sku,
            "qty": 1,
        }
    ],
    "payment_request": {
        "plan": "full",
    },
}

status, checkout = call(
    "POST",
    f"/api/stores/{tenant_a_slug}/checkout",
    checkout_body,
)

status_check(
    "Tenant A checkout",
    status,
    {200, 201},
)

order_id = ""

if isinstance(checkout, dict):

    order = checkout.get("order")

    if isinstance(order, dict):
        order_id = str(
            order.get("id")
            or order.get("order_id")
            or ""
        ).strip()


# ============================================================
# 9. VERIFY TENANT ORDER / FALLBACK ORDER ID
# ============================================================

status, tenant_orders_payload = call(
    "GET",
    "/api/customer-owner/orders",
    token=tenant_a_token,
)

status_check(
    "Tenant A orders feed",
    status,
    {200},
)

tenant_a_orders = orders_from(
    tenant_orders_payload
)

if not order_id:

    for order in tenant_a_orders:

        if str(
            order.get("buyer_email") or ""
        ).lower() == buyer_email.lower():

            order_id = str(
                order.get("id")
                or order.get("order_id")
                or ""
            ).strip()

            break

if not check(
    "Checkout order ID found",
    bool(order_id),
    order_id,
):
    print(json.dumps(checkout, indent=2, default=str))
    sys.exit(1)

check(
    "Tenant A owns checkout order",
    find_order(
        tenant_a_orders,
        order_id,
    ) is not None,
    order_id,
)


# ============================================================
# 10. VERIFY INVENTORY DROPPED
# ============================================================

status, catalog_after_checkout = call(
    "GET",
    f"/api/stores/{tenant_a_slug}/products",
)

status_check(
    "Tenant A catalog after checkout",
    status,
    {200},
)

product_after = find_product(
    products_from(catalog_after_checkout),
    sku,
)

stock_after = (
    int(product_after.get("stock") or 0)
    if product_after
    else -1
)

check(
    "Checkout reduced stock exactly once",
    stock_after == stock_before - 1,
    f"{stock_before} -> {stock_after}",
)


# ============================================================
# 11. MASTER OWNER SEES ORDER
# ============================================================

status, master_orders_payload = call(
    "GET",
    "/api/owner/orders",
    token=master_token,
)

status_check(
    "Master owner orders feed",
    status,
    {200},
)

check(
    "Master owner sees tenant order",
    find_order(
        orders_from(master_orders_payload),
        order_id,
    ) is not None,
    order_id,
)


# ============================================================
# 12. TENANT A PAYMENT FREEDOM UPDATE
# ============================================================

status, payment_update = call(
    "PUT",
    f"/api/customer-owner/payment-freedom/{order_id}",
    {
        "payment_status": "paid",
        "payment_method": "manual",
        "provider": "owner_directed",
        "payment_reference": f"QA-{STAMP}",
        "amount_cents": price_cents,
        "note": "Automated WOLF OS Phase 2 payment test.",
    },
    tenant_a_token,
)

status_check(
    "Tenant A payment update",
    status,
    {200},
)


status, payment_feed = call(
    "GET",
    "/api/customer-owner/payment-freedom",
    token=tenant_a_token,
)

status_check(
    "Tenant A Payment Freedom feed",
    status,
    {200},
)

payment_record = None

for record in payment_records_from(
    payment_feed
):
    if str(
        record.get("order_id") or ""
    ) == order_id:
        payment_record = record
        break

check(
    "Payment record exists",
    payment_record is not None,
    order_id,
)

if payment_record:

    check(
        "Payment status is paid",
        str(
            payment_record.get(
                "payment_status"
            )
            or ""
        ).lower() == "paid",
    )


# ============================================================
# 13. CREATE TENANT B
# ============================================================

tenant_b_slug = f"wolf-qa-b-{STAMP}"
tenant_b_email = f"qa-b-{STAMP}@example.com"
tenant_b_password = f"WolfQA-B-{STAMP}!"

status, tenant_b_created = call(
    "POST",
    "/api/owner/customer-accounts",
    {
        "business_name": f"WOLF QA B {STAMP}",
        "store_slug": tenant_b_slug,
        "owner_name": "WOLF QA Owner B",
        "owner_email": tenant_b_email,
        "brand": "WOLF QA B",
        "system": "WOLF OS",
        "plan": "starter",
        "temporary_password": tenant_b_password,
    },
    master_token,
)

status_check(
    "Provision tenant B",
    status,
    {201},
)


# ============================================================
# 14. TENANT B LOGIN
# ============================================================

status, tenant_b_login = call(
    "POST",
    "/api/customer-owner/login",
    {
        "email": tenant_b_email,
        "password": tenant_b_password,
        "store_slug": tenant_b_slug,
    },
)

status_check(
    "Tenant B owner login",
    status,
    {200},
)

tenant_b_token = ""

if isinstance(tenant_b_login, dict):
    tenant_b_token = str(
        tenant_b_login.get("token") or ""
    ).strip()

if not check(
    "Tenant B token",
    bool(tenant_b_token),
):
    sys.exit(1)


# ============================================================
# 15. TENANT B MUST NOT SEE TENANT A ORDER
# ============================================================

status, tenant_b_orders_payload = call(
    "GET",
    "/api/customer-owner/orders",
    token=tenant_b_token,
)

status_check(
    "Tenant B orders feed",
    status,
    {200},
)

tenant_b_orders = orders_from(
    tenant_b_orders_payload
)

check(
    "Tenant B cannot see tenant A order",
    find_order(
        tenant_b_orders,
        order_id,
    ) is None,
    order_id,
)


# ============================================================
# 16. TENANT B MUST NOT MODIFY TENANT A ORDER
# ============================================================

status, blocked_update = call(
    "PUT",
    f"/api/customer-owner/payment-freedom/{order_id}",
    {
        "payment_status": "paid",
        "payment_method": "manual",
        "provider": "owner_directed",
        "payment_reference": "CROSS-TENANT-PROBE",
        "amount_cents": price_cents,
        "note": (
            "This cross-tenant isolation probe must be rejected."
        ),
    },
    tenant_b_token,
)

check(
    "Cross-tenant payment update blocked",
    status in {403, 404},
    f"HTTP {status}",
)


# ============================================================
# 17. VERIFY TENANT A PAYMENT STILL VALID
# ============================================================

status, payment_feed_after = call(
    "GET",
    "/api/customer-owner/payment-freedom",
    token=tenant_a_token,
)

status_check(
    "Tenant A payment feed after isolation probe",
    status,
    {200},
)

payment_after = None

for record in payment_records_from(
    payment_feed_after
):
    if str(
        record.get("order_id") or ""
    ) == order_id:
        payment_after = record
        break

check(
    "Tenant A payment remains paid",
    (
        payment_after is not None
        and str(
            payment_after.get(
                "payment_status"
            )
            or ""
        ).lower() == "paid"
    ),
)


# ============================================================
# 18. DEMO STORE ISOLATION
# ============================================================

status, demo_after_payload = call(
    "GET",
    "/api/stores/demo/products",
)

status_check(
    "Demo catalog after tenant test",
    status,
    {200},
)

demo_after = snapshot_products(
    products_from(demo_after_payload)
)

check(
    "Demo product count unchanged",
    len(demo_after) == len(demo_before),
    f"{len(demo_before)} -> {len(demo_after)}",
)

check(
    "Demo inventory unchanged",
    demo_after == demo_before,
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 60)
print(" FULL TENANT REGRESSION RESULTS")
print("=" * 60)

print(f"Tenant A : {tenant_a_slug}")
print(f"Tenant B : {tenant_b_slug}")
print(f"Order    : {order_id}")
print(f"Stock    : {stock_before} -> {stock_after}")
print()

print(f"PASS: {passed}")
print(f"FAIL: {failed}")
print()

if failed:

    print(
        "WOLF OS FULL TENANT REGRESSION: FAIL"
    )

    sys.exit(1)

print(
    "WOLF OS FULL TENANT REGRESSION: PASS"
)

sys.exit(0)
