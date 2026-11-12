"""
WOLF OS V3 - Isolated Payment Transaction Ledger

Development/testing module.
Does not connect to production databases.
"""

import sqlite3
from datetime import datetime, timezone

def initialize_ledger(connection):

    connection.execute("""
        CREATE TABLE IF NOT EXISTS payment_transactions_v3 (
            transaction_id TEXT PRIMARY KEY,
            store_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            payment_reference TEXT,
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_transactions_order
        ON payment_transactions_v3(store_id, order_id)
    """)

    connection.commit()


def record_payment(
    connection,
    transaction_id,
    store_id,
    order_id,
    amount_cents,
    payment_reference=""
):

    if not isinstance(amount_cents, int) or isinstance(amount_cents, bool):
        raise ValueError("Payment must be integer cents")

    if amount_cents <= 0:
        raise ValueError("Payment must be greater than zero")

    if not all([
        transaction_id,
        store_id,
        order_id
    ]):
        raise ValueError("Transaction, store, and order IDs required")

    existing = connection.execute(
        """
        SELECT amount_cents, store_id, order_id
        FROM payment_transactions_v3
        WHERE transaction_id = ?
        """,
        (transaction_id,)
    ).fetchone()

    if existing:
        if (
            existing[0] == amount_cents
            and existing[1] == store_id
            and existing[2] == order_id
        ):
            return {"created": False, "duplicate": True}

        raise ValueError("Transaction ID conflict")

    connection.execute(
        """
        INSERT INTO payment_transactions_v3 (
            transaction_id,
            store_id,
            order_id,
            amount_cents,
            payment_reference,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            store_id,
            order_id,
            amount_cents,
            payment_reference,
            datetime.now(timezone.utc).isoformat()
        )
    )

    connection.commit()

    return {"created": True, "duplicate": False}


def payment_total(connection, store_id, order_id):

    row = connection.execute(
        """
        SELECT COALESCE(SUM(amount_cents), 0)
        FROM payment_transactions_v3
        WHERE store_id = ? AND order_id = ?
        """,
        (store_id, order_id)
    ).fetchone()

    return int(row[0])
