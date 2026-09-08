from __future__ import annotations

import asyncio

from graphone.orchestration.contracts import (
    OrchestrationPlan,
    SearchRequest,
)
from graphone.orchestration.router import (
    DatasetRouter,
)
from graphone.retrieval.job_searcher import (
    JobSearcher,
)
from graphone.retrieval.news_searcher import (
    NewsSearcher,
)


async def main() -> None:

    print(
        "=" * 80
    )

    print(
        "GRAPHONE ROUTER END-TO-END TEST"
    )

    print(
        "=" * 80
    )

    job_searcher = JobSearcher(
        file_path=(
            "data/exports/jobs.jsonl"
        )
    )

    news_searcher = NewsSearcher(
        file_path=(
            "data/exports/news.jsonl"
        )
    )

    router = DatasetRouter(
        searchers={
            "jobs": job_searcher,
            "news": news_searcher,
        }
    )

    plan = OrchestrationPlan(
        user_query=(
            "Find cybersecurity jobs and "
            "scientific literacy news"
        ),
        searches=(
            SearchRequest(
                dataset="jobs",
                query=(
                    "Find cybersecurity jobs"
                ),
                limit=5,
            ),
            SearchRequest(
                dataset="news",
                query=(
                    "Find scientific literacy news"
                ),
                limit=5,
            ),
        ),
    )

    print()

    print(
        "USER QUERY"
    )

    print(
        "-" * 80
    )

    print(
        plan.user_query
    )

    print()

    print(
        "ORCHESTRATION PLAN"
    )

    print(
        "-" * 80
    )

    for index, request in enumerate(
        plan.searches,
        start=1,
    ):

        print(
            f"{index}. Dataset: "
            f"{request.dataset}"
        )

        print(
            f"   Query: "
            f"{request.query}"
        )

        print(
            f"   Limit: "
            f"{request.limit}"
        )

    evidence = (
        await router.execute(
            plan
        )
    )

    print()

    print(
        f"TOTAL EVIDENCE RECORDS: "
        f"{len(evidence)}"
    )

    print()

    print(
        "RETRIEVED EVIDENCE"
    )

    print(
        "-" * 80
    )

    if not evidence:

        print(
            "No evidence records found."
        )

    for index, record in enumerate(
        evidence,
        start=1,
    ):

        payload = (
            record.payload
        )

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
            f"Source: "
            f"{payload.get('source')}"
        )

        print(
            f"Published: "
            f"{payload.get('published_at')}"
        )

        print(
            f"Original URL: "
            f"{payload.get('url')}"
        )

        print(
            f"Source URL: "
            f"{record.source_url}"
        )

        print(
            f"Snapshot SHA-256: "
            f"{record.raw_snapshot_sha256}"
        )

    print()

    print(
        "=" * 80
    )

    print(
        "ROUTER END-TO-END TEST COMPLETE"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )