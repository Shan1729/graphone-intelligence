from __future__ import annotations

import asyncio
from pathlib import Path

from graphone.orchestration.contracts import (
    SearchRequest,
)
from graphone.retrieval.job_searcher import (
    JobSearcher,
)


JOBS_FILE = (
    Path("data")
    / "exports"
    / "jobs.jsonl"
)


async def main() -> None:

    print("=" * 80)
    print(
        "GRAPHONE JOB RETRIEVAL TEST"
    )
    print("=" * 80)

    user_query = (
        "Find cybersecurity jobs"
    )

    print()
    print("USER QUERY")
    print("-" * 80)
    print(user_query)

    # --------------------------------------------------
    # CREATE SEARCH REQUEST
    # --------------------------------------------------

    request = SearchRequest(
        dataset="jobs",
        query=user_query,
        limit=20,
    )

    print()
    print("SEARCH REQUEST")
    print("-" * 80)

    print(
        f"Dataset: {request.dataset}"
    )

    print(
        f"Query: {request.query}"
    )

    print(
        f"Limit: {request.limit}"
    )

    # --------------------------------------------------
    # CREATE DETERMINISTIC JOB SEARCHER
    # --------------------------------------------------

    searcher = JobSearcher(
        file_path=JOBS_FILE,
    )

    # --------------------------------------------------
    # DETERMINISTIC RETRIEVAL
    # --------------------------------------------------

    evidence = await searcher.search(
        request
    )

    print()
    print(
        f"EVIDENCE RECORDS RETRIEVED: "
        f"{len(evidence)}"
    )

    # --------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------

    print()
    print(
        "FIRST 5 REAL EVIDENCE RECORDS"
    )
    print("-" * 80)

    if not evidence:

        print(
            "No matching job records were found."
        )

    else:

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
                f"Company: "
                f"{payload.get('company')}"
            )

            print(
                f"Category: "
                f"{payload.get('category')}"
            )

            print(
                f"Published: "
                f"{payload.get('published_at')}"
            )

            print(
                f"Job URL: "
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
    print("=" * 80)
    print(
        "JOB RETRIEVAL TEST COMPLETE"
    )
    print("=" * 80)


if __name__ == "__main__":

    asyncio.run(
        main()
    )