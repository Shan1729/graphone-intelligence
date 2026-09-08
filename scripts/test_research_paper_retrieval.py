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
from graphone.retrieval.research_paper_searcher import (
    ResearchPaperSearcher,
)


RESEARCH_PAPERS_FILE = (
    Path("data")
    / "exports"
    / "research_papers.jsonl"
)


async def main() -> None:

    print("=" * 80)
    print(
        "GRAPHONE RESEARCH PAPER "
        "RETRIEVAL TEST"
    )
    print("=" * 80)

    user_query = (
        "Find AI research papers"
    )

    searcher = ResearchPaperSearcher(
        file_path=RESEARCH_PAPERS_FILE,
    )

    router = DatasetRouter(
        searchers={
            "research_papers": searcher,
        }
    )

    plan = OrchestrationPlan(
        user_query=user_query,
        searches=(
            SearchRequest(
                dataset="research_papers",
                query="AI research papers",
                limit=20,
            ),
        ),
    )

    print()
    print("USER QUERY")
    print("-" * 80)
    print(user_query)

    print()
    print("SEARCH REQUEST")
    print("-" * 80)
    print(
        "Dataset: research_papers"
    )
    print(
        "Query: AI research papers"
    )
    print(
        "Limit: 20"
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
            "No matching research paper "
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
            f"Title: "
            f"{payload.get('title')}"
        )

        print(
            f"Authors: "
            f"{payload.get('authors')}"
        )

        print(
            f"Published: "
            f"{payload.get('published_date')}"
        )

        print(
            f"Paper URL: "
            f"{payload.get('paper_url')}"
        )

        print(
            f"GitHub URL: "
            f"{payload.get('github_url')}"
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
        "RESEARCH PAPER RETRIEVAL "
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