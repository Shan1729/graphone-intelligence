import pytest

from graphone.extraction.research_papers import ArxivBulkExtractor


@pytest.mark.asyncio
async def test_extract_real_research_papers():
    extractor = ArxivBulkExtractor(
        batch_size=5,
        timeout=30.0,
        max_retries=2,
    )

    papers = await extractor.extract(
        target_count=5,
    )

    assert len(papers) == 5

    for paper in papers:
        assert paper.schema_version == "1.0"
        assert paper.record_type == "RESEARCH_PAPER"
        assert paper.title
        assert paper.authors
        assert paper.paper_url.startswith("http")
        assert paper.published_date
        assert paper.source_url == paper.paper_url