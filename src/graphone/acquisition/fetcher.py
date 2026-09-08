from __future__ import annotations

import asyncio

import httpx


DEFAULT_TIMEOUT = 20.0
DEFAULT_MAX_RETRIES = 3


async def fetch_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> tuple[bytes, str, int]:
    """
    Fetch a URL asynchronously.

    Returns:

    - response content
    - final URL after redirects
    - HTTP status code

    Retries temporary failures while preserving the
    original caller-facing function contract.
    """

    last_error: Exception | None = None

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
        headers={
            "User-Agent": (
                "GraphOne-Intelligence/"
                "1.0"
            ),
        },
    ) as client:

        for attempt in range(
            max_retries + 1
        ):

            try:

                response = await client.get(
                    url
                )

                if (
                    response.status_code == 429
                    or response.status_code >= 500
                ):

                    if attempt < max_retries:

                        await asyncio.sleep(
                            2 ** attempt
                        )

                        continue

                return (
                    response.content,
                    str(response.url),
                    response.status_code,
                )

            except (
                httpx.RequestError,
                httpx.TimeoutException,
            ) as exc:

                last_error = exc

                if attempt < max_retries:

                    await asyncio.sleep(
                        2 ** attempt
                    )

                    continue

    if last_error:

        raise RuntimeError(
            f"Failed to fetch URL: "
            f"{url}"
        ) from last_error

    raise RuntimeError(
        f"Failed to fetch URL: "
        f"{url}"
    )