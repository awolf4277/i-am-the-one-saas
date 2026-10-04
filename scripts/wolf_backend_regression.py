from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


BASE = "http://127.0.0.1:5000"
PASSWORD = "WOLF-DEMO"

passed = 0
failed = 0


def call(method, path, body=None, token=None):
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
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read().decode("utf-8")

            try:
                payload = json.loads(raw)
            except Exception:
                payload = raw

            return response.status, payload

    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")

        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw

        return exc.code, payload


def check(name, actual, expected):
    global passed, failed

    if actual in expected:
        passed += 1
        print(f"[PASS] {name} -- HTTP {actual}")
        return True

    failed += 1
    print(
        f"[FAIL] {name} -- HTTP {actual}; "
        f"expected {sorted(expected)}"
    )

    return False


print()
print("============================================")
print(" WOLF OS BACKEND REGRESSION GATE")
print("============================================")
print()


# 1 HEALTH
status, health = call(
    "GET",
    "/api/health",
)

check(
    "API health",
    status,
    {200},
)


# 2 MISSING OWNER PASSWORD
status, _ = call(
    "POST",
    "/api/owner/login",
    {},
)

check(
    "Reject missing owner password",
    status,
    {401},
)


# 3 BAD OWNER PASSWORD
status, _ = call(
    "POST",
    "/api/owner/login",
    {
        "password": "NOT-THE-PASSWORD",
    },
)

check(
    "Reject bad owner password",
    status,
    {401},
)


# 4 VALID OWNER LOGIN
status, login = call(
    "POST",
    "/api/owner/login",
    {
        "password": PASSWORD,
    },
)

login_ok = check(
    "Owner login",
    status,
    {200},
)

token = ""

if login_ok and isinstance(login, dict):
    token = str(
        login.get("token") or ""
    ).strip()

if token:
    passed += 1
    print("[PASS] Owner token returned")
else:
    failed += 1
    print("[FAIL] Owner token returned")


# 5 ANONYMOUS OWNER DATA MUST FAIL
status, _ = call(
    "GET",
    "/api/owner/orders",
)

check(
    "Anonymous owner orders blocked",
    status,
    {401, 403},
)


# 6 AUTHORIZED ORDERS
if token:
    status, _ = call(
        "GET",
        "/api/owner/orders",
        token=token,
    )

    check(
        "Authorized owner orders",
        status,
        {200},
    )
else:
    failed += 1
    print("[FAIL] Authorized owner orders -- no token")


# 7 AUTHORIZED PRODUCTS
if token:
    status, _ = call(
        "GET",
        "/api/owner/products",
        token=token,
    )

    check(
        "Authorized owner products",
        status,
        {200},
    )
else:
    failed += 1
    print("[FAIL] Authorized owner products -- no token")


# 8 PUBLIC DEMO CATALOG
status, catalog = call(
    "GET",
    "/api/stores/demo/products",
)

check(
    "Public demo catalog",
    status,
    {200},
)


print()
print("============================================")
print(" REGRESSION RESULTS")
print("============================================")
print(f"PASS: {passed}")
print(f"FAIL: {failed}")
print()

if failed:
    print("WOLF OS BACKEND REGRESSION: FAIL")
    sys.exit(1)

print("WOLF OS BACKEND REGRESSION: PASS")
sys.exit(0)
