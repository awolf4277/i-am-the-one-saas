"""
WOLF OS V3 - Payment Freedom Transaction Bridge

Isolated integration service.

NOT connected to live API endpoints.

The caller must provide a store_id established by
server-side authentication, never an untrusted request field.
"""

from .payment_ledger_db_v3 import (
    insert_payment,
    calculate_received,
)

from .atomic_payment_service_v3 import (
    PaymentError,
    PaymentConflict,
    PaymentNotFound,
)


def record_payment_and_sync(
    connection,
    *,
    transaction_id,
    store_id,
    order_id,
    amount_cents,
    payment_reference="",
):
    """
    Record a payment and synchronize financial records.

    All writes use one database transaction.
    Historical payment snapshots are not auto-imported.
    """

    if not all(
        isinstance(value, str) and value.strip()
        for value in (transaction_id, store_id, order_id)
    ):
        raise PaymentError("Valid transaction, store and order IDs required")

    if type(amount_cents) is not int or amount_cents <= 0:
        raise PaymentError("Payment amount must be positive integer cents")

    transaction_id = transaction_id.strip()
    store_id = store_id.strip()
    order_id = order_id.strip()

    if not isinstance(payment_reference, str):
        raise PaymentError("Payment reference must be text")

    try:
        if not connection.is_postgres:
            connection.execute("BEGIN IMMEDIATE")

        order = connection.execute(
            """
            SELECT id, store_id, total_cents, payment_status
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

        total = int(order["total_cents"] or 0)

        if total <= 0:
            raise PaymentConflict("Invalid order total")

        plan = connection.execute(
            """
            SELECT amount_paid_cents, balance_due_cents
            FROM order_payment_plans
            WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()

        if plan is None:
            raise PaymentConflict(
                "Payment plan missing; reconciliation required"
            )

        received = calculate_received(
            connection, store_id, order_id
        )

        plan_paid = int(plan["amount_paid_cents"] or 0)
        plan_balance = int(plan["balance_due_cents"] or 0)

        snapshot = connection.execute(
            """
            SELECT amount_cents, payment_status
            FROM payment_freedom_records
            WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()

        historical_statuses = {
            "deposit_paid", "partially_paid", "paid",
            "refunded", "cancelled",
        }

        if received == 0:
            if plan_paid != 0:
                raise PaymentConflict(
                    "Historical payments require reconciliation"
                )

            if str(order["payment_status"] or "").lower() in historical_statuses:
                raise PaymentConflict(
                    "Existing order status requires reconciliation"
                )

            if snapshot:
                snapshot_status = str(
                    snapshot["payment_status"] or ""
                ).lower()

                if snapshot_status in historical_statuses:
                    raise PaymentConflict(
                        "Existing Payment Freedom history requires reconciliation"
                    )

        else:
            if plan_paid != received:
                raise PaymentConflict(
                    "Ledger and payment plan disagree"
                )

            if snapshot is None:
                raise PaymentConflict(
                    "V3 Payment Freedom snapshot missing"
                )

            if (
                int(snapshot["amount_cents"] or 0) != received
            ):
                raise PaymentConflict(
                    "Ledger and Payment Freedom snapshot disagree"
                )

        if received > 0 and plan_balance != total - received:
            raise PaymentConflict(
                "Existing balance does not match ledger"
            )

        existing = connection.execute(
            """
            SELECT store_id, order_id, amount_cents
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
                    "Transaction ID conflicts with existing payment"
                )

            connection.commit()

            return {
                "ok": True,
                "duplicate": True,
                "received_cents": received,
                "remaining_cents": total - received,
            }

        remaining = total - received

        if remaining <= 0:
            raise PaymentConflict("Order already paid")

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

        new_received = calculate_received(
            connection, store_id, order_id
        )

        new_remaining = total - new_received

        status = (
            "paid" if new_remaining == 0
            else "partially_paid"
        )

        connection.execute(
            """
            UPDATE order_payment_plans
            SET amount_paid_cents = ?,
                balance_due_cents = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
            """,
            (new_received, new_remaining, order_id),
        )

        connection.execute(
            """
            UPDATE orders
            SET payment_status = ?
            WHERE id = ? AND store_id = ?
            """,
            (status, order_id, store_id),
        )

        if snapshot:
            connection.execute(
                """
                UPDATE payment_freedom_records
                SET payment_status = ?,
                    amount_cents = ?,
                    payment_reference = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ?
                """,
                (
                    status,
                    new_received,
                    payment_reference,
                    order_id,
                ),
            )

        else:
            connection.execute(
                """
                INSERT INTO payment_freedom_records (
                    order_id,
                    payment_status,
                    amount_cents,
                    payment_reference,
                    updated_at
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    order_id,
                    status,
                    new_received,
                    payment_reference,
                ),
            )

        connection.commit()

        return {
            "ok": True,
            "duplicate": False,
            "transaction_id": transaction_id,
            "received_cents": new_received,
            "remaining_cents": new_remaining,
            "payment_status": status,
        }

    except Exception:
        connection.rollback()
        raise
