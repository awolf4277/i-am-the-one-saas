import importlib.util
import sqlite3

spec = importlib.util.spec_from_file_location(
    "payment_ledger_db_v3",
    "backend/app/payment_ledger_db_v3.py"
)

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row

module.create_ledger_schema(db)
db.commit()

module.insert_payment(
    db, "TX-100", "STORE-A", "ORD-100", 150000
)

module.insert_payment(
    db, "TX-101", "STORE-A", "ORD-100", 100000
)

assert module.calculate_received(
    db, "STORE-A", "ORD-100"
) == 250000

print("PASS: Cumulative payment totals")

assert module.calculate_received(
    db, "STORE-B", "ORD-100"
) == 0

print("PASS: Tenant-scoped totals")

try:
    module.insert_payment(
        db, "TX-100", "STORE-A", "ORD-100", 150000
    )
except sqlite3.IntegrityError:
    print("PASS: Duplicate transaction rejected")
    db.rollback()
else:
    raise AssertionError("Duplicate transaction accepted")

db.commit()

module.insert_payment(
    db, "TX-102", "STORE-A", "ORD-100", 50000
)

db.rollback()

assert module.calculate_received(
    db, "STORE-A", "ORD-100"
) == 0

print("PASS: Transaction rollback")

db.close()

print()
print("WOLF OS V3 DATABASE LEDGER: 4/4 PASS")
