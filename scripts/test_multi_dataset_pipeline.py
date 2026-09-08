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
from graphone.retrieval.research_paper_searcher import (
    ResearchPaperSearcher,
)
from graphone.retrieval.startup_searcher import (
    StartupSearcher,
)


STARTUPS_FILE = (
    Path("data")
    / "exports"
    / "startups.jsonl"
)


PRODUCTS_FILE = (
    Path("data")
    / "exports"
    / "products.jsonl"
)


RESEARCH_PAPERS_FILE = (
    Path("data")
    / "exports"
    / "research_papers.jsonl"
)


async def main() -> None:

    print("=" * 80)
    print(
        "GRAPHONE MULTI-DATASET "
        "INTELLIGENCE PIPELINE TEST"
    )
    print("=" * 80)

    user_query = (
        "Find AI startups working on AI agents and research papers on AI agents"
        
    )

    print()
    print("USER QUERY")
    print("-" * 80)
    print(user_query)

    # --------------------------------------------------
    # STEP 1: GEMINI PLANNING
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
    # STEP 2: SEARCHER REGISTRATION
    # --------------------------------------------------

    print()
    print(
        "STEP 2: REGISTER "
        "DETERMINISTIC SEARCHERS"
    )
    print("-" * 80)

    startup_searcher = (
        StartupSearcher(
            file_path=STARTUPS_FILE,
        )
    )

    product_searcher = (
        ProductSearcher(
            file_path=PRODUCTS_FILE,
        )
    )

    research_paper_searcher = (
        ResearchPaperSearcher(
            file_path=RESEARCH_PAPERS_FILE,
        )
    )

    router = DatasetRouter(
        searchers={
            "startups": startup_searcher,
            "products": product_searcher,
            "research_papers": (
                research_paper_searcher
            ),
        }
    )

    print(
        "Registered datasets:"
    )

    for dataset in sorted(
        router.searchers.keys()
    ):

        print(
            f"- {dataset}"
        )

    # --------------------------------------------------
    # STEP 3: DETERMINISTIC RETRIEVAL
    # --------------------------------------------------

    print()
    print(
        "STEP 3: DETERMINISTIC "
        "MULTI-DATASET RETRIEVAL"
    )
    print("-" * 80)

    evidence = await router.execute(
        plan
    )

    print(
        f"Evidence records retrieved: "
        f"{len(evidence)}"
    )

    evidence_by_dataset: dict[
        str,
        int,
    ] = {}

    for record in evidence:

        evidence_by_dataset[
            record.dataset
        ] = (
            evidence_by_dataset.get(
                record.dataset,
                0,
            )
            + 1
        )

    print()
    print(
        "RETRIEVAL BREAKDOWN"
    )

    for (
        dataset,
        count,
    ) in sorted(
        evidence_by_dataset.items()
    ):

        print(
            f"{dataset}: "
            f"{count} records"
        )

    # --------------------------------------------------
    # STEP 4: GROUNDED RESPONSE
    # --------------------------------------------------

    print()
    print(
        "STEP 4: GROUNDED RESPONSE "
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
    # FINAL ANSWER
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

    # --------------------------------------------------
    # GROUNDING SUMMARY
    # --------------------------------------------------

    print()
    print("=" * 80)
    print(
        "GROUNDING SUMMARY"
    )
    print("=" * 80)

    print(
        "Evidence records attached: "
        f"{len(grounded_response.evidence)}"
    )

    datasets_used = sorted(
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
            datasets_used
        )
    )

    print()

    print(
        "Gemini selected datasets "
        "through a constrained plan."
    )

    print(
        "The deterministic router executed "
        "only registered dataset searchers."
    )

    print(
        "The final answer was generated "
        "from retrieved GraphOne evidence."
    )

    print()

    print("=" * 80)
    print(
        "GRAPHONE MULTI-DATASET "
        "PIPELINE TEST COMPLETE"
    )
    print("=" * 80)


if __name__ == "__main__":

    asyncio.run(
        main()
    )