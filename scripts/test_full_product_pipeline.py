from __future__ import annotations

import asyncio
from pathlib import Path

from graphone.orchestration.gemini_planner import (
    GeminiPlanner,
)
from graphone.orchestration.grounded_responder import (
    GroundedResponder,
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
        "GRAPHONE FULL PRODUCT "
        "INTELLIGENCE PIPELINE TEST"
    )
    print("=" * 80)

    user_query = (
        "Find chocolate products"
    )

    print()
    print("USER QUERY")
    print("-" * 80)
    print(user_query)

    # --------------------------------------------------
    # STEP 1
    # --------------------------------------------------

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
        f"Normalized user query: "
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

    # --------------------------------------------------
    # STEP 2
    # --------------------------------------------------

    print()
    print(
        "STEP 2: DETERMINISTIC "
        "RETRIEVAL"
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

    print(
        f"Evidence records retrieved: "
        f"{len(evidence)}"
    )

    # --------------------------------------------------
    # STEP 3
    # --------------------------------------------------

    print()
    print(
        "STEP 3: GROUNDED RESPONSE "
        "GENERATION"
    )
    print("-" * 80)

    responder = (
        GroundedResponder()
    )

    grounded_response = (
        await responder.generate(
            user_query=user_query,
            evidence=evidence,
        )
    )

    # --------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------

    print()
    print("=" * 80)
    print(
        "FINAL GROUNDED ANSWER"
    )
    print("=" * 80)

    print()
    print(
        grounded_response.answer
    )

    print()
    print("=" * 80)
    print(
        "GROUNDING SUMMARY"
    )
    print("=" * 80)

    print(
        f"Evidence records attached: "
        f"{len(grounded_response.evidence)}"
    )

    datasets = sorted(
        {
            record.dataset
            for record in (
                grounded_response.evidence
            )
        }
    )

    print(
        "Datasets used: "
        + ", ".join(
            datasets
        )
    )

    print()
    print(
        "All retrieved evidence remains "
        "attached to the final response."
    )

    print(
        "The final answer was generated "
        "from retrieved GraphOne evidence."
    )

    print()
    print("=" * 80)
    print(
        "FULL GRAPHONE PRODUCT "
        "PIPELINE TEST COMPLETE"
    )
    print("=" * 80)


if __name__ == "__main__":

    asyncio.run(
        main()
    )