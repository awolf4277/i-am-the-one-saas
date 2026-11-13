import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db_compat import DatabaseConnection
from app.payment_ledger_db_v3 import create_ledger_schema
from app.atomic_payment_service_v3 import (
    record_atomic_payment,
    PaymentConflict,
    PaymentNotFound,
)


raw = sqlite3.connect(":memory:")
raw.row_factory = sqlite3.Row
db = DatabaseConnection(raw, "sqlite")

passed = 0


def check(label, condition):
    global passed
    assert condition, label
    passed += 1
    print(f"PASS: {label}")


try:
    db.execute("""
        CREATE TABLE orders (
            id TEXT PRIMARY KEY,
            store_id TEXT NOT NULL,
            total_cents INTEGER NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE order_payment_plans (
            order_id TEXT PRIMARY KEY,
            amount_paid_cents INTEGER NOT NULL DEFAULT 0
        )
    """)

    db.execute("""
        CREATE TABLE payment_freedom_records (
            order_id TEXT PRIMARY KEY,
            amount_cents INTEGER NOT NULL DEFAULT 0,
            payment_status TEXT NOT NULL DEFAULT 'unpaid'
        )
    """)

    create_ledger_schema(db)

    db.execute("""
        INSERT INTO orders
        (id, store_id, total_cents)
        VALUES (?, ?, ?)
    """, ("ORD-001", "STORE-A", 500000))

    db.execute("""
        INSERT INTO orders
        (id, store_id, total_cents)
        VALUES (?, ?, ?)
    """, ("ORD-002", "STORE-B", 100000))

    db.execute("""
        INSERT INTO orders
        (id, store_id, total_cents)
        VALUES (?, ?, ?)
    """, ("ORD-003", "STORE-A", 100000))

    db.execute("""
        INSERT INTO order_payment_plans
        (order_id, amount_paid_cents)
        VALUES (?, ?)
    """, ("ORD-003", 25000))

    db.commit()

    first = record_atomic_payment(
        db,
        transaction_id="TX-001",
        store_id="STORE-A",
        order_id="ORD-001",
        amount_cents=150000,
    )

    check(
        "First deposit recorded",
        first["received_cents"] == 150000
        and first["remaining_cents"] == 350000
    )

    second = record_atomic_payment(
        db,
        transaction_id="TX-002",
        store_id="STORE-A",
        order_id="ORD-001",
        amount_cents=100000,
    )

    check(
        "Cumulative payments calculated",
        second["received_cents"] == 250000
        and second["remaining_cents"] == 250000
    )

    duplicate = record_atomic_payment(
        db,
        transaction_id="TX-001",
        store_id="STORE-A",
        order_id="ORD-001",
        amount_cents=150000,
    )

    check(
        "Duplicate retry does not double-charge",
        duplicate["duplicate"]
        and duplicate["received_cents"] == 250000
    )

    try:
        record_atomic_payment(
            db,
            transaction_id="TX-003",
            store_id="STORE-A",
            order_id="ORD-001",
            amount_cents=300000,
        )
    except PaymentConflict:
        overpayment_blocked = True
    else:
        overpayment_blocked = False

    check("Overpayment rejected", overpayment_blocked)

    try:
        record_atomic_payment(
            db,
            transaction_id="TX-004",
            store_id="STORE-B",
            order_id="ORD-001",
            amount_cents=10000,
        )
    except PaymentNotFound:
        tenant_blocked = True
    else:
        tenant_blocked = False

    check("Cross-tenant payment rejected", tenant_blocked)

    try:
        record_atomic_payment(
            db,
            transaction_id="TX-005",
            store_id="STORE-A",
            order_id="ORD-003",
            amount_cents=10000,
        )
    except PaymentConflict:
        legacy_blocked = True
    else:
        legacy_blocked = False

    check(
        "Existing payment history protected",
        legacy_blocked
    )

    final = record_atomic_payment(
        db,
        transaction_id="TX-006",
        store_id="STORE-A",
        order_id="ORD-001",
        amount_cents=250000,
    )

    check(
        "Final payment closes balance",
        final["received_cents"] == 500000
        and final["remaining_cents"] == 0
        and final["payment_status"] == "paid"
    )

    print()
    print("=" * 50)
    print(f"WOLF OS V3 ATOMIC PAYMENT TESTS: {passed}/7 PASS")
    print("=" * 50)

    assert passed == 7

finally:
    db.close()
