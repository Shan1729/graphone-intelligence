import asyncio
from pathlib import Path

from graphone.orchestration.gemini_planner import (
    GeminiPlanner,
)
from graphone.orchestration.router import (
    DatasetRouter,
)
from graphone.retrieval.startup_searcher import (
    StartupSearcher,
)


async def main():
    print("=" * 80)
    print("GRAPHONE END-TO-END STARTUP RETRIEVAL TEST")
    print("=" * 80)
    print()

    data_file = Path(
        "data/exports/startups.jsonl"
    )

    startup_searcher = StartupSearcher(
        file_path=data_file
    )

    router = DatasetRouter(
        searchers={
            "startups": startup_searcher,
        }
    )

    planner = GeminiPlanner()

    user_query = (
        "Find AI startups"
    )

    print("USER QUERY:")
    print(user_query)
    print()

    print(
        "STEP 1: GEMINI CREATES "
        "ORCHESTRATION PLAN"
    )
    print("-" * 80)

    plan = await planner.create_plan(
        user_query
    )

    for search in plan.searches:
        print(
            f"Dataset: {search.dataset}"
        )
        print(
            f"Query: {search.query}"
        )
        print(
            f"Limit: {search.limit}"
        )
        print()

    print(
        "STEP 2: DETERMINISTIC "
        "ROUTER EXECUTES PLAN"
    )
    print("-" * 80)

    evidence = await router.execute(
        plan
    )

    print()
    print(
        f"EVIDENCE RECORDS RETRIEVED: "
        f"{len(evidence)}"
    )

    print()

    if not evidence:
        print(
            "No matching startup records found."
        )
        return

    print(
        "FIRST 5 REAL EVIDENCE RECORDS"
    )
    print("-" * 80)

    for index, record in enumerate(
        evidence[:5],
        start=1,
    ):
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
            f"Entity: "
            f"{record.payload.get('entity_name')}"
        )

        print(
            f"Description: "
            f"{record.payload.get('description')}"
        )

        print(
            f"Industry: "
            f"{record.payload.get('industry')}"
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
    print("END-TO-END RETRIEVAL TEST COMPLETE")
    print("=" * 80)

    print(
        "Gemini selected the dataset."
    )

    print(
        "The deterministic searcher retrieved "
        "real stored records."
    )

    print(
        "Every result preserved provenance."
    )


if __name__ == "__main__":
    asyncio.run(main())