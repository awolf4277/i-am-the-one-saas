import importlib.util
import sqlite3

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

compat = load_module(
    "db_compat",
    "backend/app/db_compat.py"
)

ledger = load_module(
    "payment_ledger_db_v3",
    "backend/app/payment_ledger_db_v3.py"
)

raw = sqlite3.connect(":memory:")
raw.row_factory = sqlite3.Row

db = compat.DatabaseConnection(raw, "sqlite")

passed = 0

def check(name, condition):
    global passed
    assert condition, name
    passed += 1
    print(f"PASS: {name}")

try:
    ledger.create_ledger_schema(db)
    db.commit()

    ledger.insert_payment(
        db, "TX-001", "STORE-A", "ORD-001", 150000
    )

    ledger.insert_payment(
        db, "TX-002", "STORE-A", "ORD-001", 100000
    )

    db.commit()

    check(
        "Committed cumulative payments",
        ledger.calculate_received(
            db, "STORE-A", "ORD-001"
        ) == 250000
    )

    ledger.insert_payment(
        db, "TX-003", "STORE-A", "ORD-001", 50000
    )

    db.rollback()

    check(
        "Rollback preserves committed payments",
        ledger.calculate_received(
            db, "STORE-A", "ORD-001"
        ) == 250000
    )

    try:
        ledger.insert_payment(
            db, "TX-001", "STORE-A", "ORD-001", 150000
        )
    except sqlite3.IntegrityError:
        db.rollback()
        duplicate_rejected = True
    else:
        duplicate_rejected = False

    check(
        "Duplicate transaction rejected",
        duplicate_rejected
    )

    check(
        "Failed insert preserves balance",
        ledger.calculate_received(
            db, "STORE-A", "ORD-001"
        ) == 250000
    )

    check(
        "Tenant isolation",
        ledger.calculate_received(
            db, "STORE-B", "ORD-001"
        ) == 0
    )

    check(
        "PostgreSQL placeholder conversion",
        compat.DatabaseConnection(
            raw, "postgresql"
        )._prepare(
            "SELECT * FROM payment_transactions_v3 WHERE store_id = ?"
        ).count("%s") == 1
    )

    print()
    print("=" * 45)
    print(f"WOLF OS V3 ADAPTER CERTIFICATION: {passed}/6 PASS")
    print("=" * 45)

    if passed != 6:
        raise SystemExit(1)

finally:
    db.close()
