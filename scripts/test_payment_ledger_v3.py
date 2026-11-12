import importlib.util
from pathlib import Path

engine_path = Path("backend/app/payment_ledger_v3.py")

spec = importlib.util.spec_from_file_location(
    "payment_ledger_v3",
    engine_path
)

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

calculate_balance = module.calculate_balance
calculate_collection_priority = module.calculate_collection_priority

passed = 0

def check(name, condition):
    global passed
    if not condition:
        raise AssertionError(name)
    passed += 1
    print(f"PASS: {name}")

result = calculate_balance(450000, [150000, 100000])

check(
    "Cumulative payments",
    result["received_cents"] == 250000
)

check(
    "Remaining balance",
    result["balance_due_cents"] == 200000
)

result = calculate_balance(49900, [20000, 29900])

check(
    "Fully paid order",
    result["is_paid"] is True
)

result = calculate_balance(29900, [])

check(
    "Unpaid order",
    result["balance_due_cents"] == 29900
)

try:
    calculate_balance(10000, [8000, 5000])
except ValueError:
    check("Overpayment protection", True)
else:
    raise AssertionError("Overpayment protection failed")

orders = [
    {
        "id": "ORD-001",
        "buyer_name": "Buyer A",
        "balance_due_cents": 50000,
        "payment_status": "unpaid"
    },
    {
        "id": "ORD-002",
        "buyer_name": "Buyer B",
        "balance_due_cents": 200000,
        "payment_status": "partially_paid"
    },
    {
        "id": "ORD-003",
        "buyer_name": "Buyer C",
        "balance_due_cents": 0,
        "payment_status": "paid"
    }
]

ranked = calculate_collection_priority(orders)

check(
    "Highest balance first",
    ranked[0]["order_id"] == "ORD-002"
)

check(
    "Paid orders excluded",
    len(ranked) == 2
)

print()
print("=" * 45)
print(f"WOLF OS V3 TEST RESULTS: {passed}/7 PASS")
print("=" * 45)

if passed != 7:
    raise SystemExit(1)
