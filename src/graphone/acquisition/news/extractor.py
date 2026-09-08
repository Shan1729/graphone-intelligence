from __future__ import annotations

import asyncio
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus

from graphone.acquisition.cas import store_snapshot
from graphone.acquisition.fetcher import fetch_url


GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search"
)

OUTPUT_FILE = (
    Path("data")
    / "exports"
    / "news.jsonl"
)

ATOM_NAMESPACE = {
    "atom": (
        "http://www.w3.org/2005/Atom"
    ),
}


class NewsExtractor:
    """
    Extract real recent news records.

    Only articles published within the previous
    24 hours are accepted.

    Raw source responses are stored in GraphOne CAS
    and every exported record receives the snapshot
    SHA-256 for provenance.
    """

    def __init__(
        self,
        query: str = "artificial intelligence",
        max_retries: int = 3,
    ) -> None:

        self.query = query
        self.max_retries = max_retries

    def _build_url(
        self,
    ) -> str:

        search_query = (
            f"{self.query} when:1d"
        )

        encoded_query = quote_plus(
            search_query
        )

        return (
            f"{GOOGLE_NEWS_RSS}"
            f"?q={encoded_query}"
            f"&hl=en-IN"
            f"&gl=IN"
            f"&ceid=IN:en"
        )

    def _parse_datetime(
        self,
        value: str,
    ) -> datetime | None:

        try:

            parsed = (
                parsedate_to_datetime(
                    value
                )
            )

            if parsed.tzinfo is None:

                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(
                timezone.utc
            )

        except (
            ValueError,
            TypeError,
            IndexError,
        ):

            return None

    def _is_within_24_hours(
        self,
        published_at: datetime,
    ) -> bool:

        now = datetime.now(
            timezone.utc
        )

        cutoff = (
            now
            - timedelta(hours=24)
        )

        return (
            cutoff
            <= published_at
            <= now
        )

    async def extract(
        self,
        limit: int = 20,
    ) -> list[dict]:

        if limit < 1:

            raise ValueError(
                "limit must be >= 1"
            )

        source_url = (
            self._build_url()
        )

        last_error: Exception | None = None

        for attempt in range(
            self.max_retries
        ):

            try:

                (
                    content,
                    final_url,
                    status_code,
                ) = await fetch_url(
                    source_url
                )

                if status_code != 200:

                    raise RuntimeError(
                        "News source returned "
                        f"HTTP {status_code}"
                    )

                snapshot = (
                    store_snapshot(
                        content=content,
                        source_url=final_url,
                        content_type=(
                            "application/rss+xml"
                        ),
                    )
                )

                root = ET.fromstring(
                    content
                )

                channel = root.find(
                    "channel"
                )

                if channel is None:

                    raise RuntimeError(
                        "Invalid RSS feed: "
                        "channel not found"
                    )

                records: list[
                    dict
                ] = []

                seen_urls: set[
                    str
                ] = set()

                for item in channel.findall(
                    "item"
                ):

                    title_element = (
                        item.find(
                            "title"
                        )
                    )

                    link_element = (
                        item.find(
                            "link"
                        )
                    )

                    source_element = (
                        item.find(
                            "source"
                        )
                    )

                    published_element = (
                        item.find(
                            "pubDate"
                        )
                    )

                    if (
                        title_element is None
                        or link_element is None
                        or published_element is None
                    ):

                        continue

                    title = (
                        title_element.text
                        or ""
                    ).strip()

                    url = (
                        link_element.text
                        or ""
                    ).strip()

                    published_raw = (
                        published_element.text
                        or ""
                    ).strip()

                    if (
                        not title
                        or not url
                        or url in seen_urls
                    ):

                        continue

                    published_at = (
                        self._parse_datetime(
                            published_raw
                        )
                    )

                    if (
                        published_at is None
                    ):

                        continue

                    if not (
                        self._is_within_24_hours(
                            published_at
                        )
                    ):

                        continue

                    source = (
                        "Google News"
                    )

                    if (
                        source_element is not None
                        and source_element.text
                    ):

                        source = (
                            source_element.text
                            .strip()
                        )

                    record = {
                        "schema_version": "1.0",
                        "record_type": "NEWS",
                        "title": title,
                        "url": url,
                        "source": source,
                        "published_at": (
                            published_at
                            .isoformat()
                        ),
                        "item_type": "news",
                        "source_url": (
                            final_url
                        ),
                        "raw_snapshot_sha256": (
                            snapshot.sha256
                        ),
                    }

                    records.append(
                        record
                    )

                    seen_urls.add(
                        url
                    )

                    if (
                        len(records)
                        >= limit
                    ):

                        break

                return records

            except Exception as exc:

                last_error = exc

                if (
                    attempt
                    < self.max_retries - 1
                ):

                    await asyncio.sleep(
                        2 ** attempt
                    )

        raise RuntimeError(
            "Failed to extract news: "
            f"{last_error}"
        )


async def extract_news_to_jsonl(
    limit: int = 20,
) -> list[dict]:

    extractor = NewsExtractor()

    records = await extractor.extract(
        limit=limit
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        for record in records:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return records