import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from graphone.extraction.startups import YCStartupExtractor


OUTPUT_DIR = Path("data/exports")
OUTPUT_FILE = OUTPUT_DIR / "startups.jsonl"


async def main():
    target_count = 1000

    print("=" * 80)
    print("GRAPHONE STARTUP BULK EXTRACTION")
    print("=" * 80)
    print(f"Target records: {target_count}")
    print("Source: Y Combinator public company dataset")
    print()

    extractor = YCStartupExtractor(
        timeout=60.0,
        max_retries=4,
    )

    started_at = datetime.now(timezone.utc)

    startups = await extractor.extract(
        target_count=target_count,
    )

    finished_at = datetime.now(timezone.utc)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        for startup in startups:
            file.write(
                json.dumps(
                    asdict(startup),
                    ensure_ascii=False,
                )
                + "\n"
            )

    duration = (
        finished_at - started_at
    ).total_seconds()

    print()
    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Records extracted: {len(startups)}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Started at: {started_at.isoformat()}")
    print(f"Finished at: {finished_at.isoformat()}")
    print(f"Duration: {duration:.2f} seconds")

    if startups:
        print()
        print("FIRST RECORD")
        print("-" * 80)
        print(
            json.dumps(
                asdict(startups[0]),
                indent=2,
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())