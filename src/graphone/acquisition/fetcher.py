from __future__ import annotations

import httpx


DEFAULT_TIMEOUT = 20.0


async def fetch_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[bytes, str, int]:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
    ) as client:
        response = await client.get(url)

    return response.content, str(response.url), response.status_code