from __future__ import annotations

import asyncio

from graphone.acquisition.news.extractor import (
    extract_news_to_jsonl,
)


async def main() -> None:

    print("=" * 80)
    print(
        "GRAPHONE 24-HOUR NEWS BULK ACQUISITION"
    )
    print("=" * 80)

    records = await extract_news_to_jsonl()

    print()

    print(
        f"Fresh news found in previous 24 hours: "
        f"{len(records)}"
    )

    print(
        "News dataset acquisition COMPLETE"
    )

    print()

    for index, record in enumerate(
        records[:10],
        start=1,
    ):

        print(
            f"{index}. {record['title']}"
        )

        print(
            f"   Source: "
            f"{record['source']}"
        )

        print(
            f"   Published: "
            f"{record['published_at']}"
        )

        print(
            f"   Source URL: "
            f"{record['source_url']}"
        )

        print(
            f"   Snapshot: "
            f"{record['raw_snapshot_sha256']}"
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )