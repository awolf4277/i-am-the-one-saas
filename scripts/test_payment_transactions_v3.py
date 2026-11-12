import importlib.util
import sqlite3

spec = importlib.util.spec_from_file_location(
    "payment_transactions_v3",
    "backend/app/payment_transactions_v3.py"
)

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

db = sqlite3.connect(":memory:")

module.initialize_ledger(db)

passed = 0

def check(name, condition):
    global passed

    if not condition:
        raise AssertionError(name)

    passed += 1
    print(f"PASS: {name}")


# TEST 1 - MULTIPLE PAYMENTS

module.record_payment(
    db,
    "TX-001",
    "STORE-A",
    "ORD-001",
    150000
)

module.record_payment(
    db,
    "TX-002",
    "STORE-A",
    "ORD-001",
    100000
)

check(
    "Multiple payments accumulate",
    module.payment_total(
        db,
        "STORE-A",
        "ORD-001"
    ) == 250000
)


# TEST 2 - DUPLICATE PROTECTION

duplicate = module.record_payment(
    db,
    "TX-001",
    "STORE-A",
    "ORD-001",
    150000
)

check(
    "Duplicate transaction prevented",
    duplicate["duplicate"] is True
    and module.payment_total(
        db,
        "STORE-A",
        "ORD-001"
    ) == 250000
)


# TEST 3 - TENANT ISOLATION

check(
    "Tenant payment isolation",
    module.payment_total(
        db,
        "STORE-B",
        "ORD-001"
    ) == 0
)


# TEST 4 - TRANSACTION ID CONFLICT

try:
    module.record_payment(
        db,
        "TX-001",
        "STORE-A",
        "ORD-001",
        999999
    )

except ValueError:
    check(
        "Transaction ID conflict rejected",
        True
    )

else:
    raise AssertionError(
        "Transaction ID conflict was accepted"
    )


# FINAL RESULTS

print()
print("=" * 45)
print(
    f"WOLF OS V3 TRANSACTION LEDGER: {passed}/4 PASS"
)
print("=" * 45)

if passed != 4:
    raise SystemExit(1)

db.close()
