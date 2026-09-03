import pytest

from src.graphone.pipeline.news_jobs import NewsJobItem


def test_news_job_item():
    item = NewsJobItem(
        title="Test Article",
        url="https://example.com/article",
        source="Example",
        published_at="2026-08-30T21:00:00",
        item_type="news",
    )

    assert item.title == "Test Article"
    assert item.url == "https://example.com/article"
    assert item.source == "Example"
    assert item.item_type == "news"

def test_news_and_job_types():
    news = NewsJobItem(
        title="AI News",
        url="https://example.com/news",
        source="Example News",
        published_at="2026-08-30T21:00:00",
        item_type="news",
    )

    job = NewsJobItem(
        title="AI Engineer",
        url="https://example.com/job",
        source="Example Jobs",
        published_at="2026-08-30T21:00:00",
        item_type="job",
    )

    assert news.item_type == "news"
    assert job.item_type == "job"

def test_invalid_item_type():
    with pytest.raises(ValueError):
        NewsJobItem(
            title="Invalid",
            url="https://example.com",
            source="Example",
            published_at="2026-08-30T21:00:00",
            item_type="random",
        )