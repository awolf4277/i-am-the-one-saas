import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db_compat import DatabaseConnection
from app.payment_ledger_db_v3 import (
    create_ledger_schema,
    calculate_received,
)
from app.payment_freedom_bridge_v3 import record_payment_and_sync
from app.atomic_payment_service_v3 import (
    PaymentConflict,
    PaymentNotFound,
)


raw = sqlite3.connect(":memory:")
raw.row_factory = sqlite3.Row

db = DatabaseConnection(raw, "sqlite")

passed = 0


def check(name, condition):
    global passed
    assert condition, name
    passed += 1
    print(f"PASS: {name}")


def get_plan(order_id):
    return db.execute(
        """
        SELECT amount_paid_cents, balance_due_cents
        FROM order_payment_plans
        WHERE order_id = ?
        """,
        (order_id,),
    ).fetchone()


def get_order_status(order_id):
    row = db.execute(
        "SELECT payment_status FROM orders WHERE id = ?",
        (order_id,),
    ).fetchone()
    return row["payment_status"]


def get_snapshot(order_id):
    return db.execute(
        """
        SELECT payment_status, amount_cents
        FROM payment_freedom_records
        WHERE order_id = ?
        """,
        (order_id,),
    ).fetchone()


try:
    db.execute("""
        CREATE TABLE orders (
            id TEXT PRIMARY KEY,
            store_id TEXT NOT NULL,
            total_cents INTEGER NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'unpaid'
        )
    """)

    db.execute("""
        CREATE TABLE order_payment_plans (
            order_id TEXT PRIMARY KEY,
            payment_plan TEXT NOT NULL DEFAULT 'full',
            deposit_percent INTEGER NOT NULL DEFAULT 100,
            amount_due_now_cents INTEGER NOT NULL DEFAULT 0,
            amount_paid_cents INTEGER NOT NULL DEFAULT 0,
            balance_due_cents INTEGER NOT NULL DEFAULT 0,
            payment_terms TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE payment_freedom_records (
            order_id TEXT PRIMARY KEY,
            payment_status TEXT NOT NULL DEFAULT 'unpaid',
            payment_method TEXT NOT NULL DEFAULT 'manual',
            provider TEXT NOT NULL DEFAULT 'owner_directed',
            payment_link TEXT NOT NULL DEFAULT '',
            payment_reference TEXT NOT NULL DEFAULT '',
            amount_cents INTEGER NOT NULL DEFAULT 0,
            note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    create_ledger_schema(db)

    for order_id, store_id, total in [
        ("ORD-100", "STORE-A", 450000),
        ("ORD-200", "STORE-B", 100000),
        ("ORD-300", "STORE-A", 100000),
        ("ORD-400", "STORE-A", 100000),
        ("ORD-500", "STORE-A", 100000),
    ]:
        db.execute(
            """
            INSERT INTO orders (
                id, store_id, total_cents, payment_status
            )
            VALUES (?, ?, ?, 'unpaid')
            """,
            (order_id, store_id, total),
        )

        if order_id != "ORD-400":
            db.execute(
                """
                INSERT INTO order_payment_plans (
                    order_id,
                    amount_paid_cents,
                    balance_due_cents
                )
                VALUES (?, 0, ?)
                """,
                (order_id, total),
            )

    # Simulate historical payment data.
    db.execute(
        """
        UPDATE order_payment_plans
        SET amount_paid_cents = 25000,
            balance_due_cents = 75000
        WHERE order_id = 'ORD-300'
        """
    )

    # Existing unpaid snapshot for rollback testing.
    db.execute(
        """
        INSERT INTO payment_freedom_records (
            order_id, payment_status, amount_cents
        )
        VALUES ('ORD-500', 'unpaid', 0)
        """
    )

    db.commit()

    first = record_payment_and_sync(
        db,
        transaction_id="V3-TX-001",
        store_id="STORE-A",
        order_id="ORD-100",
        amount_cents=150000,
        payment_reference="DEPOSIT-001",
    )

    check(
        "First deposit recorded",
        first["received_cents"] == 150000
        and first["remaining_cents"] == 300000,
    )

    second = record_payment_and_sync(
        db,
        transaction_id="V3-TX-002",
        store_id="STORE-A",
        order_id="ORD-100",
        amount_cents=100000,
        payment_reference="PARTIAL-002",
    )

    check(
        "Multiple payments accumulate",
        second["received_cents"] == 250000
        and second["remaining_cents"] == 200000,
    )

    plan = get_plan("ORD-100")

    check(
        "Payment plan synchronized",
        int(plan["amount_paid_cents"]) == 250000
        and int(plan["balance_due_cents"]) == 200000,
    )

    snapshot = get_snapshot("ORD-100")

    check(
        "Payment Freedom synchronized",
        int(snapshot["amount_cents"]) == 250000
        and snapshot["payment_status"] == "partially_paid",
    )

    check(
        "Order status synchronized",
        get_order_status("ORD-100") == "partially_paid",
    )

    duplicate = record_payment_and_sync(
        db,
        transaction_id="V3-TX-001",
        store_id="STORE-A",
        order_id="ORD-100",
        amount_cents=150000,
    )

    check(
        "Duplicate retry is idempotent",
        duplicate["duplicate"] is True
        and duplicate["received_cents"] == 250000,
    )

    try:
        record_payment_and_sync(
            db,
            transaction_id="V3-TX-001",
            store_id="STORE-A",
            order_id="ORD-100",
            amount_cents=50000,
        )
    except PaymentConflict:
        conflict_blocked = True
    else:
        conflict_blocked = False

    check(
        "Conflicting transaction ID rejected",
        conflict_blocked,
    )

    try:
        record_payment_and_sync(
            db,
            transaction_id="V3-TX-003",
            store_id="STORE-A",
            order_id="ORD-100",
            amount_cents=300000,
        )
    except PaymentConflict:
        overpayment_blocked = True
    else:
        overpayment_blocked = False

    check(
        "Overpayment rejected",
        overpayment_blocked,
    )

    try:
        record_payment_and_sync(
            db,
            transaction_id="V3-TX-004",
            store_id="STORE-B",
            order_id="ORD-100",
            amount_cents=10000,
        )
    except PaymentNotFound:
        tenant_blocked = True
    else:
        tenant_blocked = False

    check(
        "Cross-tenant payment rejected",
        tenant_blocked,
    )

    try:
        record_payment_and_sync(
            db,
            transaction_id="V3-TX-005",
            store_id="STORE-A",
            order_id="ORD-300",
            amount_cents=10000,
        )
    except PaymentConflict:
        legacy_blocked = True
    else:
        legacy_blocked = False

    check(
        "Historical payment protected",
        legacy_blocked,
    )

    try:
        record_payment_and_sync(
            db,
            transaction_id="V3-TX-006",
            store_id="STORE-A",
            order_id="ORD-400",
            amount_cents=10000,
        )
    except PaymentConflict:
        missing_plan_blocked = True
    else:
        missing_plan_blocked = False

    check(
        "Missing payment plan rejected",
        missing_plan_blocked,
    )

    # Force the snapshot update to fail.
    # This must roll back the ledger insert and plan update.
    db.execute("""
        CREATE TRIGGER reject_v3_snapshot_update
        BEFORE UPDATE ON payment_freedom_records
        WHEN NEW.order_id = 'ORD-500'
        BEGIN
            SELECT RAISE(ABORT, 'Simulated snapshot failure');
        END
    """)

    db.commit()

    failure_detected = False

    try:
        record_payment_and_sync(
            db,
            transaction_id="V3-TX-ROLLBACK",
            store_id="STORE-A",
            order_id="ORD-500",
            amount_cents=25000,
        )
    except sqlite3.DatabaseError:
        failure_detected = True

    check(
        "Simulated database failure detected",
        failure_detected,
    )

    rollback_plan = get_plan("ORD-500")
    rollback_snapshot = get_snapshot("ORD-500")

    check(
        "Failed payment rolled back completely",
        calculate_received(db, "STORE-A", "ORD-500") == 0
        and int(rollback_plan["amount_paid_cents"]) == 0
        and int(rollback_plan["balance_due_cents"]) == 100000
        and int(rollback_snapshot["amount_cents"]) == 0
        and get_order_status("ORD-500") == "unpaid",
    )

    final = record_payment_and_sync(
        db,
        transaction_id="V3-TX-007",
        store_id="STORE-A",
        order_id="ORD-100",
        amount_cents=200000,
    )

    check(
        "Final payment closes order",
        final["received_cents"] == 450000
        and final["remaining_cents"] == 0
        and final["payment_status"] == "paid"
        and get_order_status("ORD-100") == "paid",
    )

    print()
    print("=" * 55)
    print(f"WOLF OS V3 PAYMENT BRIDGE TESTS: {passed}/14 PASS")
    print("=" * 55)

    assert passed == 14

finally:
    db.close()
