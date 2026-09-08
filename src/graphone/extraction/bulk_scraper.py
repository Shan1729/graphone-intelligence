from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from graphone.acquisition.cas import store_snapshot
from graphone.acquisition.fetcher import fetch_url
from graphone.storage.db import init_db, record_acquisition


@dataclass(frozen=True)
class BulkFetchResult:
    source_url: str
    final_url: str | None
    status_code: int | None
    sha256: str | None
    success: bool
    error: str | None


class BulkScraper:
    """
    High-concurrency bulk acquisition engine.

    Designed for large one-time extraction workloads.
    Concurrency can be increased through configuration without
    changing the scraper logic.
    """

    def __init__(
        self,
        concurrency: int = 20,
        timeout: float = 20.0,
        max_retries: int = 4,
        base_backoff: float = 1.0,
    ) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be >= 1")

        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")

        self._semaphore = asyncio.Semaphore(concurrency)
        self.timeout = timeout
        self.max_retries = max_retries
        self.base_backoff = base_backoff

    async def _fetch_with_retry(
        self,
        url: str,
    ) -> BulkFetchResult:
        """
        Fetch a single URL with bounded concurrency and retry handling.
        """

        last_error: str | None = None

        for attempt in range(self.max_retries + 1):
            try:
                async with self._semaphore:
                    content, final_url, status_code = await fetch_url(
                        url=url,
                        timeout=self.timeout,
                    )

                # Retry temporary failures.
                if status_code == 429 or 500 <= status_code < 600:
                    last_error = f"HTTP {status_code}"

                    if attempt < self.max_retries:
                        delay = (
                            self.base_backoff * (2 ** attempt)
                            + random.uniform(0, 1)
                        )

                        await asyncio.sleep(delay)
                        continue

                # Reject all remaining non-success responses.
                if not 200 <= status_code < 300:
                    return BulkFetchResult(
                        source_url=url,
                        final_url=final_url,
                        status_code=status_code,
                        sha256=None,
                        success=False,
                        error=f"HTTP {status_code}",
                    )

                # Store raw source content with provenance.
                snapshot = store_snapshot(
                    content=content,
                    source_url=final_url,
                )

                # Record acquisition state.
                recorded = record_acquisition(
                    sha256=snapshot.sha256,
                    source_url=final_url,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )

                # Duplicate snapshots are still valid successful acquisitions.
                return BulkFetchResult(
                    source_url=url,
                    final_url=final_url,
                    status_code=status_code,
                    sha256=snapshot.sha256,
                    success=True,
                    error=None if recorded else "duplicate_snapshot",
                )

            except Exception as exc:
                last_error = str(exc)

                if attempt < self.max_retries:
                    delay = (
                        self.base_backoff * (2 ** attempt)
                        + random.uniform(0, 1)
                    )

                    await asyncio.sleep(delay)

        return BulkFetchResult(
            source_url=url,
            final_url=None,
            status_code=None,
            sha256=None,
            success=False,
            error=last_error,
        )

    async def fetch_many(
        self,
        urls: Iterable[str],
    ) -> list[BulkFetchResult]:
        """
        Concurrently acquire a collection of URLs.

        Concurrency is bounded by the configured semaphore.
        """

        init_db()

        tasks = [
            asyncio.create_task(
                self._fetch_with_retry(url)
            )
            for url in urls
        ]

        if not tasks:
            return []

        return await asyncio.gather(*tasks)