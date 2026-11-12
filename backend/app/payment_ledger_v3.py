"""
WOLF OS Collection Command V3
Payment calculation utilities.

This module does not modify the database.
"""

from decimal import Decimal, InvalidOperation


def validate_cents(value):
    """Validate an integer monetary amount in cents."""

    if isinstance(value, bool):
        raise ValueError("Boolean amounts are invalid")

    if not isinstance(value, int):
        raise ValueError("Payment amount must be an integer")

    if value < 0:
        raise ValueError("Payment amount cannot be negative")

    return value


def calculate_balance(total_cents, payments):
    """
    Calculate outstanding balance from individual payments.

    payments must contain unique, verified transactions.
    """

    total = validate_cents(total_cents)

    received = 0

    for payment in payments:
        received += validate_cents(payment)

    if received > total:
        raise ValueError(
            "Payments exceed the original order total"
        )

    return {
        "total_cents": total,
        "received_cents": received,
        "balance_due_cents": total - received,
        "payment_count": len(payments),
        "is_paid": received == total,
    }


def calculate_collection_priority(orders):
    """
    Rank outstanding orders by highest balance.

    Input orders must have verified balance_due_cents values.
    """

    candidates = []

    for order in orders:

        status = str(
            order.get("payment_status", "unpaid")
        ).lower()

        if status in {
            "paid",
            "refunded",
            "cancelled",
            "canceled",
        }:
            continue

        balance = validate_cents(
            order.get("balance_due_cents", 0)
        )

        if balance <= 0:
            continue

        candidates.append({
            "order_id": order.get("id"),
            "buyer_name": order.get("buyer_name"),
            "balance_due_cents": balance,
            "payment_status": status,
        })

    return sorted(
        candidates,
        key=lambda item: item["balance_due_cents"],
        reverse=True,
    )
