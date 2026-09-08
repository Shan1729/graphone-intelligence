import pytest

from graphone.extraction.startups import YCStartupExtractor


@pytest.mark.asyncio
async def test_extract_real_startups():
    extractor = YCStartupExtractor(
        timeout=60.0,
        max_retries=2,
    )

    startups = await extractor.extract(
        target_count=5,
    )

    assert len(startups) == 5

    names = set()

    for startup in startups:
        assert startup.schema_version == "1.0"
        assert startup.record_type == "STARTUP"
        assert startup.source_name == "Y Combinator"
        assert startup.source_url.startswith("http")
        assert startup.entity_name
        assert startup.raw_snapshot_sha256
        assert startup.collected_at

        names.add(
            startup.entity_name.casefold()
        )

    assert len(names) == 5