from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil


ROOT = Path(r"X:\i-am-the-one-saas")
TARGET = ROOT / "frontend" / "src" / "components" / "RevenueCommandCenter.tsx"

BACKUP_DIR = (
    ROOT
    / "backups"
    / "revenue-engine-pricing"
    / datetime.now().strftime("%Y%m%d-%H%M%S")
)

OFFERS = (
    ("Starter Storefront", 499, 1500),
    ("Pro Storefront + Dashboard", 1500, 4500),
    ("Custom SaaS Buildout", 5000, 9000),
)


def update_offer_price(
    source: str,
    offer_name: str,
    old_price: int,
    new_price: int,
) -> str:
    name_pattern = re.compile(
        rf'name\s*:\s*["\']{re.escape(offer_name)}["\']'
    )

    name_match = name_pattern.search(source)

    if not name_match:
        raise RuntimeError(
            f'Offer not found: {offer_name}'
        )

    object_start = source.rfind(
        "{",
        max(0, name_match.start() - 800),
        name_match.start(),
    )

    object_end = source.find("},", name_match.end())

    if object_start == -1 or object_end == -1:
        raise RuntimeError(
            f'Could not isolate offer block: {offer_name}'
        )

    object_end += 2
    block = source[object_start:object_end]

    field_pattern = re.compile(
        rf'('
        rf'\b(?:price|amount|startingPrice|basePrice|priceValue|value)'
        rf'\s*:\s*'
        rf')'
        rf'{old_price}'
        rf'(\b)'
    )

    updated_block, count = field_pattern.subn(
        rf'\g<1>{new_price}\g<2>',
        block,
        count=1,
    )

    if count == 0:
        numeric_matches = list(
            re.finditer(
                rf'(?<![\d.]){old_price}(?![\d.])',
                block,
            )
        )

        if len(numeric_matches) != 1:
            print(
                f"\n--- BLOCK INSPECTION: {offer_name} ---"
            )
            print(block)
            print("--- END BLOCK ---\n")

            raise RuntimeError(
                f'Expected one numeric {old_price} value '
                f'for {offer_name}, found {len(numeric_matches)}.'
            )

        match = numeric_matches[0]

        updated_block = (
            block[:match.start()]
            + str(new_price)
            + block[match.end():]
        )

    print(
        f"{offer_name}: "
        f"${old_price:,}+ -> ${new_price:,}+"
    )

    return (
        source[:object_start]
        + updated_block
        + source[object_end:]
    )


if not TARGET.exists():
    raise SystemExit(f"Missing target: {TARGET}")

text = TARGET.read_text(encoding="utf-8")

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
shutil.copy2(TARGET, BACKUP_DIR / TARGET.name)

for offer_name, old_price, new_price in OFFERS:
    text = update_offer_price(
        text,
        offer_name,
        old_price,
        new_price,
    )

TARGET.write_text(
    text,
    encoding="utf-8",
    newline="\n",
)

print("\nRevenue Engine premium pricing aligned.")
print(f"Backup: {BACKUP_DIR}")
