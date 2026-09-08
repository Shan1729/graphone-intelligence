from __future__ import annotations

import asyncio

from graphone.orchestration.contracts import (
    SearchRequest,
)
from graphone.retrieval.news_searcher import (
    NewsSearcher,
)


async def main() -> None:

    print(
        "=" * 80
    )

    print(
        "GRAPHONE NEWS RETRIEVAL TEST"
    )

    print(
        "=" * 80
    )

    user_query = (
        "Find scientific literacy news"
    )

    print()

    print(
        "USER QUERY"
    )

    print(
        "-" * 80
    )

    print(
        user_query
    )

    request = SearchRequest(
        dataset="news",
        query=user_query,
        limit=20,
    )

    print()

    print(
        "SEARCH REQUEST"
    )

    print(
        "-" * 80
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

    searcher = NewsSearcher(
        file_path=(
            "data/exports/news.jsonl"
        )
    )

    evidence = (
        await searcher.search(
            request
        )
    )

    print()

    print(
        f"EVIDENCE RECORDS RETRIEVED: "
        f"{len(evidence)}"
    )

    print()

    print(
        "FIRST 5 REAL EVIDENCE RECORDS"
    )

    print(
        "-" * 80
    )

    if not evidence:

        print(
            "No matching news records "
            "were found."
        )

    for index, item in enumerate(
        evidence[:5],
        start=1,
    ):

        payload = item.payload

        print()

        print(
            f"RESULT {index}"
        )

        print(
            f"Record ID: "
            f"{item.record_id}"
        )

        print(
            f"Dataset: "
            f"{item.dataset}"
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
            f"News URL: "
            f"{payload.get('url')}"
        )

        print(
            f"Source URL: "
            f"{item.source_url}"
        )

        print(
            f"Snapshot SHA-256: "
            f"{item.raw_snapshot_sha256}"
        )

    print()

    print(
        "=" * 80
    )

    print(
        "NEWS RETRIEVAL TEST COMPLETE"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )