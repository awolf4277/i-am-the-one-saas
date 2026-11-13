"""
WOLF OS V3 - Atomic Payment Service

Isolated backend service.
Not connected to production payment endpoints.

The authenticated caller must supply the verified store_id.
Requires the V3 ledger schema to exist.
"""

from .payment_ledger_db_v3 import (
    insert_payment,
    calculate_received,
)


class PaymentError(Exception):
    pass


class PaymentConflict(PaymentError):
    pass


class PaymentNotFound(PaymentError):
    pass


def record_atomic_payment(
    connection,
    *,
    transaction_id,
    store_id,
    order_id,
    amount_cents,
    payment_reference="",
):
    """
    Record one payment against a verified order.

    Uses a database transaction and order-level locking
    where supported.

    Existing legacy payments must be reconciled first.
    """

    if not all(
        isinstance(value, str) and value.strip()
        for value in (transaction_id, store_id, order_id)
    ):
        raise PaymentError("Valid transaction, store and order IDs required")

    transaction_id = transaction_id.strip()
    store_id = store_id.strip()
    order_id = order_id.strip()

    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
        raise PaymentError("Payment amount must be integer cents")

    if amount_cents <= 0:
        raise PaymentError("Payment amount must be positive")

    try:
        if not connection.is_postgres:
            connection.execute("BEGIN IMMEDIATE")

        order = connection.execute(
            """
            SELECT id, store_id, total_cents
            FROM orders
            WHERE id = ?
              AND store_id = ?
            FOR UPDATE
            """,
            (order_id, store_id),
        ).fetchone()

        if order is None:
            raise PaymentNotFound(
                "Order not found for authenticated store"
            )

        total_cents = int(order["total_cents"])

        if total_cents <= 0:
            raise PaymentConflict("Order total must be positive")

        # Existing snapshot payments are not automatically imported.
        # Block new payments until historical amounts are reconciled.
        legacy_plan = connection.execute(
            """
            SELECT amount_paid_cents
            FROM order_payment_plans
            WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()

        if legacy_plan and int(
            legacy_plan["amount_paid_cents"] or 0
        ) > 0:
            raise PaymentConflict(
                "Existing payment plan requires V3 reconciliation"
            )

        legacy_record = connection.execute(
            """
            SELECT amount_cents, payment_status
            FROM payment_freedom_records
            WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()

        if legacy_record:
            legacy_amount = int(
                legacy_record["amount_cents"] or 0
            )

            legacy_status = str(
                legacy_record["payment_status"] or ""
            ).lower()

            if legacy_amount > 0 or legacy_status in {
                "paid",
                "deposit_paid",
                "partially_paid",
            }:
                raise PaymentConflict(
                    "Existing Payment Freedom record requires reconciliation"
                )

        # Check idempotency before calculating a new balance.
        existing = connection.execute(
            """
            SELECT transaction_id, store_id, order_id, amount_cents
            FROM payment_transactions_v3
            WHERE transaction_id = ?
            """,
            (transaction_id,),
        ).fetchone()

        if existing:
            if (
                existing["store_id"] != store_id
                or existing["order_id"] != order_id
                or int(existing["amount_cents"]) != amount_cents
            ):
                raise PaymentConflict(
                    "Transaction ID belongs to different payment details"
                )

            received = calculate_received(
                connection, store_id, order_id
            )

            connection.commit()

            return {
                "ok": True,
                "duplicate": True,
                "transaction_id": transaction_id,
                "received_cents": received,
                "remaining_cents": max(
                    0, total_cents - received
                ),
            }

        received = calculate_received(
            connection, store_id, order_id
        )

        remaining = total_cents - received

        if remaining <= 0:
            raise PaymentConflict("Order already fully paid")

        if amount_cents > remaining:
            raise PaymentConflict(
                "Payment exceeds remaining balance"
            )

        insert_payment(
            connection,
            transaction_id,
            store_id,
            order_id,
            amount_cents,
            payment_reference,
        )

        updated_received = calculate_received(
            connection, store_id, order_id
        )

        updated_remaining = total_cents - updated_received

        connection.commit()

        return {
            "ok": True,
            "duplicate": False,
            "transaction_id": transaction_id,
            "received_cents": updated_received,
            "remaining_cents": updated_remaining,
            "payment_status": (
                "paid"
                if updated_remaining == 0
                else "partially_paid"
            ),
        }

    except Exception:
        connection.rollback()
        raise
