import asyncio

from graphone.extraction.startups import YCStartupExtractor


async def main():
    extractor = YCStartupExtractor(
        timeout=60.0,
        max_retries=2,
    )

    startups = await extractor.extract(
        target_count=5,
    )

    for index, startup in enumerate(startups, start=1):
        print("\n" + "=" * 80)
        print(f"STARTUP {index}")
        print("=" * 80)
        print(f"Name: {startup.entity_name}")
        print(f"Company URL: {startup.company_url}")
        print(f"Website: {startup.website}")
        print(f"Description: {startup.description}")
        print(f"Industry: {startup.industry}")
        print(f"Location: {startup.location}")
        print(f"Employee Count: {startup.employee_count}")
        print(f"Source: {startup.source_name}")
        print(f"Source URL: {startup.source_url}")
        print(f"Snapshot SHA-256: {startup.raw_snapshot_sha256}")
        print(f"Collected At: {startup.collected_at}")


if __name__ == "__main__":
    asyncio.run(main())