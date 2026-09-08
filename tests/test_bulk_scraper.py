import pytest

from graphone.extraction.bulk_scraper import BulkScraper


@pytest.mark.asyncio
async def test_fetch_many_success():
    scraper = BulkScraper(
        concurrency=2,
        timeout=10.0,
        max_retries=1,
    )

    urls = [
        "https://example.com",
        "https://httpbin.org/get",
    ]

    results = await scraper.fetch_many(urls)

    assert len(results) == 2

    assert all(
        result.success
        for result in results
    )

    assert all(
        result.status_code == 200
        for result in results
    )

    assert all(
        result.sha256 is not None
        for result in results
    )