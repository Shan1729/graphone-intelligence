import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from graphone.extraction.products import (
    OpenFoodFactsProductExtractor,
)


OUTPUT_DIR = Path("data/exports")
OUTPUT_FILE = OUTPUT_DIR / "products.jsonl"


async def main():
    target_count = 1000

    print("=" * 80)
    print("GRAPHONE PRODUCT BULK EXTRACTION")
    print("=" * 80)
    print(f"Target records: {target_count}")
    print("Source: Open Food Facts")
    print()

    extractor = OpenFoodFactsProductExtractor(
        page_size=100,
        timeout=60.0,
        max_retries=8,
    )

    started_at = datetime.now(timezone.utc)

    products = await extractor.extract(
        target_count=target_count,
    )

    finished_at = datetime.now(timezone.utc)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        for product in products:
            file.write(
                json.dumps(
                    asdict(product),
                    ensure_ascii=False,
                )
                + "\n"
            )

    duration = (
        finished_at - started_at
    ).total_seconds()

    print()
    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)

    print(
        f"Records extracted: "
        f"{len(products)}"
    )

    print(
        f"Output file: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Started at: "
        f"{started_at.isoformat()}"
    )

    print(
        f"Finished at: "
        f"{finished_at.isoformat()}"
    )

    print(
        f"Duration: "
        f"{duration:.2f} seconds"
    )

    if len(products) < target_count:
        print()
        print(
            "WARNING: Fewer records than the "
            "requested target were extracted."
        )

    if products:
        print()
        print("FIRST RECORD")
        print("-" * 80)

        print(
            json.dumps(
                asdict(products[0]),
                indent=2,
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())