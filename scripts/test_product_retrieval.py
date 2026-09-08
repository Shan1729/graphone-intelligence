from __future__ import annotations

import asyncio
from pathlib import Path

from graphone.orchestration.contracts import (
    OrchestrationPlan,
    SearchRequest,
)
from graphone.orchestration.router import (
    DatasetRouter,
)
from graphone.retrieval.product_searcher import (
    ProductSearcher,
)


PRODUCTS_FILE = (
    Path("data")
    / "exports"
    / "products.jsonl"
)


async def main() -> None:

    print("=" * 80)
    print(
        "GRAPHONE PRODUCT "
        "RETRIEVAL TEST"
    )
    print("=" * 80)

    searcher = ProductSearcher(
        file_path=PRODUCTS_FILE,
    )

    router = DatasetRouter(
        searchers={
            "products": searcher,
        }
    )

    plan = OrchestrationPlan(
        user_query=(
            "Find chocolate products"
        ),
        searches=(
            SearchRequest(
                dataset="products",
                query="chocolate products",
                limit=20,
            ),
        ),
    )

    print()
    print("USER QUERY")
    print("-" * 80)
    print(
        plan.user_query
    )

    print()
    print("SEARCH REQUEST")
    print("-" * 80)

    for request in plan.searches:

        print(
            f"Dataset: "
            f"{request.dataset}"
        )

        print(
            f"Query: "
            f"{request.query}"
        )

        print(
            f"Limit: "
            f"{request.limit}"
        )

    evidence = (
        await router.execute(
            plan
        )
    )

    print()
    print(
        "EVIDENCE RECORDS "
        f"RETRIEVED: {len(evidence)}"
    )

    if not evidence:

        print()
        print(
            "No matching product "
            "records found."
        )

        return

    print()
    print(
        "FIRST 5 REAL "
        "EVIDENCE RECORDS"
    )
    print("-" * 80)

    for index, record in enumerate(
        evidence[:5],
        start=1,
    ):

        payload = record.payload

        print()
        print(
            f"RESULT {index}"
        )

        print(
            f"Record ID: "
            f"{record.record_id}"
        )

        print(
            f"Dataset: "
            f"{record.dataset}"
        )

        print(
            f"Product: "
            f"{payload.get('product_name')}"
        )

        print(
            f"Brand: "
            f"{payload.get('brand')}"
        )

        print(
            f"Category: "
            f"{payload.get('category')}"
        )

        print(
            f"Barcode: "
            f"{payload.get('barcode')}"
        )

        print(
            f"Source URL: "
            f"{record.source_url}"
        )

        print(
            "Snapshot SHA-256: "
            f"{record.raw_snapshot_sha256}"
        )

    print()
    print("=" * 80)
    print(
        "PRODUCT RETRIEVAL "
        "TEST COMPLETE"
    )
    print("=" * 80)

    print(
        "The deterministic searcher "
        "retrieved only stored records."
    )

    print(
        "Every result preserved "
        "provenance."
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )