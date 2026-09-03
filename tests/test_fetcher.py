import httpx
import pytest

from src.graphone.acquisition.fetcher import fetch_url


@pytest.mark.asyncio
async def test_fetcher_handles_200(monkeypatch):
    async def fake_get(self, url):
        return httpx.Response(
            200,
            content=b"Hello world",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    content, final_url, status_code = await fetch_url(
        "https://example.com"
    )

    assert status_code == 200
    assert content == b"Hello world"
    assert final_url == "https://example.com"


@pytest.mark.asyncio
async def test_fetcher_handles_429(monkeypatch):
    async def fake_get(self, url):
        return httpx.Response(
            429,
            content=b"Too many requests",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    content, final_url, status_code = await fetch_url(
        "https://example.com"
    )

    assert status_code == 429
    assert content == b"Too many requests"
    assert final_url == "https://example.com"


@pytest.mark.asyncio
async def test_fetcher_handles_500(monkeypatch):
    async def fake_get(self, url):
        return httpx.Response(
            500,
            content=b"Server error",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    content, final_url, status_code = await fetch_url(
        "https://example.com"
    )

    assert status_code == 500
    assert content == b"Server error"
    assert final_url == "https://example.com"


@pytest.mark.asyncio
async def test_fetcher_times_out(monkeypatch):
    async def fake_get(self, url):
        raise httpx.TimeoutException("Request timed out")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    with pytest.raises(httpx.TimeoutException):
        await fetch_url(
            "https://example.com",
            timeout=0.1,
        )