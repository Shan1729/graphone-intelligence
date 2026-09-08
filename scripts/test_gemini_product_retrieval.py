from __future__ import annotations

import asyncio
from pathlib import Path

from graphone.orchestration.gemini_planner import (
    GeminiPlanner,
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
        "GRAPHONE GEMINI → PRODUCT "
        "END-TO-END RETRIEVAL TEST"
    )
    print("=" * 80)

    user_query = (
        "Find chocolate products"
    )

    print()
    print("USER QUERY")
    print("-" * 80)
    print(user_query)

    print()
    print(
        "STEP 1: GEMINI CREATES "
        "ORCHESTRATION PLAN"
    )
    print("-" * 80)

    planner = GeminiPlanner()

    plan = await planner.create_plan(
        user_query=user_query,
    )

    print(
        f"User query: "
        f"{plan.user_query}"
    )

    print()
    print("SEARCH REQUESTS")

    for index, request in enumerate(
        plan.searches,
        start=1,
    ):

        print()

        print(
            f"Search {index}"
        )

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

    print()
    print(
        "STEP 2: DETERMINISTIC "
        "ROUTER EXECUTES PLAN"
    )
    print("-" * 80)

    product_searcher = (
        ProductSearcher(
            file_path=PRODUCTS_FILE,
        )
    )

    router = DatasetRouter(
        searchers={
            "products": (
                product_searcher
            ),
        }
    )

    evidence = await router.execute(
        plan
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
        "END-TO-END PRODUCT "
        "RETRIEVAL TEST COMPLETE"
    )
    print("=" * 80)

    print(
        "Gemini selected the dataset."
    )

    print(
        "The deterministic searcher "
        "retrieved real stored records."
    )

    print(
        "Every result preserved "
        "provenance."
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )