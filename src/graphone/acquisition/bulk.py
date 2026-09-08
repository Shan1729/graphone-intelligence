from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

import httpx


DEFAULT_CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class BulkDownload:
    """
    Result of a completed bulk download.
    """

    source_url: str
    output_path: Path
    size_bytes: int


async def download_bulk_file(
    source_url: str,
    output_path: Path,
    timeout: float = 120.0,
    max_retries: int = 5,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> BulkDownload:
    """
    Download a large source artifact using streaming.

    The entire remote file is never loaded into
    Python memory at once.

    Data is streamed in fixed-size chunks directly
    to disk, making the acquisition approach suitable
    for very large datasets.
    """

    if chunk_size < 1:
        raise ValueError(
            "chunk_size must be >= 1"
        )

    if max_retries < 0:
        raise ValueError(
            "max_retries must be >= 0"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".part"
    )

    last_error: Exception | None = None

    for attempt in range(
        max_retries + 1
    ):
        try:
            timeout_config = httpx.Timeout(
                timeout
            )

            async with httpx.AsyncClient(
                timeout=timeout_config,
                follow_redirects=True,
            ) as client:

                async with client.stream(
                    "GET",
                    source_url,
                    headers={
                        "User-Agent": (
                            "GraphOneIntelligence/1.0 "
                            "(bulk-data-acquisition)"
                        )
                    },
                ) as response:

                    if (
                        response.status_code == 429
                        or response.status_code >= 500
                    ):
                        raise httpx.HTTPStatusError(
                            (
                                "Retryable HTTP error: "
                                f"{response.status_code}"
                            ),
                            request=response.request,
                            response=response,
                        )

                    response.raise_for_status()

                    bytes_written = 0

                    with temporary_path.open(
                        "wb"
                    ) as file:

                        async for chunk in (
                            response.aiter_bytes(
                                chunk_size=chunk_size
                            )
                        ):
                            if not chunk:
                                continue

                            file.write(chunk)

                            bytes_written += len(
                                chunk
                            )

            temporary_path.replace(
                output_path
            )

            return BulkDownload(
                source_url=source_url,
                output_path=output_path,
                size_bytes=bytes_written,
            )

        except Exception as exc:
            last_error = exc

            if temporary_path.exists():
                temporary_path.unlink()

            if attempt < max_retries:

                wait_seconds = min(
                    60,
                    5 * (
                        2 ** attempt
                    ),
                )

                print(
                    f"Bulk download failed: "
                    f"{type(exc).__name__}. "
                    f"Retry "
                    f"{attempt + 1}/"
                    f"{max_retries}. "
                    f"Waiting "
                    f"{wait_seconds} seconds..."
                )

                await asyncio.sleep(
                    wait_seconds
                )

    raise RuntimeError(
        "Failed to download bulk source "
        f"after {max_retries + 1} attempts: "
        f"{last_error}"
    )