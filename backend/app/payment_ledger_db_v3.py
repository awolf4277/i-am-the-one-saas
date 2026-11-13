"""
WOLF OS V3 - Database-Compatible Payment Ledger

Designed for the existing database adapter.
Does not connect to production.
"""

from datetime import datetime, timezone


def create_ledger_schema(connection):

    connection.execute("""
        CREATE TABLE IF NOT EXISTS payment_transactions_v3 (
            transaction_id TEXT PRIMARY KEY,
            store_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            amount_cents BIGINT NOT NULL CHECK(amount_cents > 0),
            payment_reference TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_payment_transactions_v3_order
        ON payment_transactions_v3(store_id, order_id)
    """)


def insert_payment(
    connection,
    transaction_id,
    store_id,
    order_id,
    amount_cents,
    payment_reference=""
):

    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
        raise ValueError("Payment amount must be integer cents")

    if amount_cents <= 0:
        raise ValueError("Payment amount must be positive")

    if not all(
        isinstance(value, str) and value.strip()
        for value in (transaction_id, store_id, order_id)
    ):
        raise ValueError("Valid IDs required")

    connection.execute("""
        INSERT INTO payment_transactions_v3 (
            transaction_id,
            store_id,
            order_id,
            amount_cents,
            payment_reference,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        transaction_id.strip(),
        store_id.strip(),
        order_id.strip(),
        amount_cents,
        payment_reference,
        datetime.now(timezone.utc).isoformat()
    ))


def calculate_received(connection, store_id, order_id):

    row = connection.execute("""
        SELECT COALESCE(SUM(amount_cents), 0) AS received_cents
        FROM payment_transactions_v3
        WHERE store_id = ?
          AND order_id = ?
    """, (store_id, order_id)).fetchone()

    return int(row["received_cents"])
