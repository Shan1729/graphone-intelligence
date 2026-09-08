import asyncio

from graphone.extraction.research_papers import ArxivBulkExtractor


async def main():
    extractor = ArxivBulkExtractor(
        batch_size=5,
        timeout=30.0,
        max_retries=2,
    )

    papers = await extractor.extract(
        target_count=5,
    )

    for index, paper in enumerate(papers, start=1):
        print("\n" + "=" * 80)
        print(f"PAPER {index}")
        print("=" * 80)
        print(f"Title: {paper.title}")
        print(f"Authors: {', '.join(paper.authors)}")
        print(f"Paper URL: {paper.paper_url}")
        print(f"Published: {paper.published_date}")
        print(f"GitHub URL: {paper.github_url}")
        print(f"GitHub Stars: {paper.github_stars}")
        print(f"Source URL: {paper.source_url}")


if __name__ == "__main__":
    asyncio.run(main())