from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from graphone.acquisition.cas import store_snapshot
from graphone.acquisition.fetcher import fetch_url

from graphone.acquisition.jobs.source_registry import (
    GREENHOUSE_BOARDS,
    LEVER_SITES,
    REMOTIVE_API_URL,
    greenhouse_url,
    lever_url,
)


OUTPUT_FILE = (
    Path("data")
    / "exports"
    / "jobs.jsonl"
)


class JobExtractor:
    """
    One-time multi-source bulk acquisition for jobs.

    Sources are acquired only during dataset creation.

    Retrieval later uses the local jobs.jsonl dataset
    and does not call external job sources.
    """

    def __init__(
        self,
        max_retries: int = 3,
    ) -> None:

        self.max_retries = max_retries

    def _parse_datetime(
        self,
        value: str,
    ) -> datetime | None:

        if not value:
            return None

        try:

            normalized = (
                value.strip()
                .replace("Z", "+00:00")
            )

            parsed = datetime.fromisoformat(
                normalized
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
            AttributeError,
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
            <= now + timedelta(minutes=5)
        )

    def _build_record(
        self,
        *,
        title: str,
        url: str,
        company: str,
        category: str,
        published_at: datetime,
        source_name: str,
        source_url: str,
        snapshot_sha256: str,
    ) -> dict:

        return {
            "schema_version": "1.0",
            "record_type": "JOB",
            "title": title.strip(),
            "url": url.strip(),
            "source": source_name,
            "published_at": (
                published_at.isoformat()
            ),
            "item_type": "job",
            "company": company.strip(),
            "category": category.strip(),
            "source_url": source_url,
            "raw_snapshot_sha256": (
                snapshot_sha256
            ),
        }

    async def _fetch_source(
        self,
        url: str,
    ) -> tuple[bytes, str] | None:

        for attempt in range(
            self.max_retries
        ):

            try:

                (
                    content,
                    final_url,
                    status_code,
                ) = await fetch_url(
                    url
                )

                if status_code != 200:

                    raise RuntimeError(
                        f"HTTP {status_code}"
                    )

                return (
                    content,
                    final_url,
                )

            except Exception as exc:

                print(
                    f"Source fetch failed "
                    f"({attempt + 1}/"
                    f"{self.max_retries}): "
                    f"{url}"
                )

                print(
                    f"Reason: {exc}"
                )

                if (
                    attempt
                    < self.max_retries - 1
                ):

                    await asyncio.sleep(
                        2 ** attempt
                    )

        print(
            f"Skipping unavailable source: "
            f"{url}"
        )

        return None

    async def _extract_remotive(
        self,
    ) -> list[dict]:

        print()
        print(
            "Fetching Remotive..."
        )

        fetched = await self._fetch_source(
            REMOTIVE_API_URL
        )

        if fetched is None:

            return []

        content, final_url = fetched

        snapshot = store_snapshot(
            content=content,
            source_url=final_url,
            content_type="application/json",
        )

        payload = json.loads(
            content.decode("utf-8")
        )

        jobs = payload.get(
            "jobs",
            [],
        )

        records: list[dict] = []

        for job in jobs:

            if not isinstance(
                job,
                dict,
            ):
                continue

            title = str(
                job.get(
                    "title",
                    "",
                )
            ).strip()

            url = str(
                job.get(
                    "url",
                    "",
                )
            ).strip()

            published_raw = job.get(
                "publication_date"
            )

            published_at = (
                self._parse_datetime(
                    str(
                        published_raw
                        or ""
                    )
                )
            )

            if (
                not title
                or not url
                or published_at is None
                or not self._is_within_24_hours(
                    published_at
                )
            ):
                continue

            records.append(
                self._build_record(
                    title=title,
                    url=url,
                    company=str(
                        job.get(
                            "company_name",
                            "",
                        )
                    ),
                    category=str(
                        job.get(
                            "category",
                            "",
                        )
                    ),
                    published_at=published_at,
                    source_name="Remotive",
                    source_url=final_url,
                    snapshot_sha256=(
                        snapshot.sha256
                    ),
                )
            )

        print(
            f"Remotive qualifying jobs: "
            f"{len(records)}"
        )

        return records

    async def _extract_greenhouse_board(
        self,
        board_token: str,
    ) -> list[dict]:

        url = greenhouse_url(
            board_token
        )

        print()
        print(
            f"Fetching Greenhouse board: "
            f"{board_token}"
        )

        fetched = await self._fetch_source(
            url
        )

        if fetched is None:

            return []

        content, final_url = fetched

        snapshot = store_snapshot(
            content=content,
            source_url=final_url,
            content_type="application/json",
        )

        payload = json.loads(
            content.decode("utf-8")
        )

        jobs = payload.get(
            "jobs",
            [],
        )

        records: list[dict] = []

        for job in jobs:

            if not isinstance(
                job,
                dict,
            ):
                continue

            title = str(
                job.get(
                    "title",
                    "",
                )
            ).strip()

            url = str(
                job.get(
                    "absolute_url",
                    "",
                )
            ).strip()

            updated_raw = (
                job.get("updated_at")
                or job.get("created_at")
            )

            published_at = (
                self._parse_datetime(
                    str(
                        updated_raw
                        or ""
                    )
                )
            )

            if (
                not title
                or not url
                or published_at is None
                or not self._is_within_24_hours(
                    published_at
                )
            ):
                continue

            location = job.get(
                "location",
                {}
            )

            if isinstance(
                location,
                dict,
            ):

                category = str(
                    location.get(
                        "name",
                        "",
                    )
                )

            else:

                category = ""

            records.append(
                self._build_record(
                    title=title,
                    url=url,
                    company=board_token,
                    category=category,
                    published_at=published_at,
                    source_name=(
                        f"Greenhouse:{board_token}"
                    ),
                    source_url=final_url,
                    snapshot_sha256=(
                        snapshot.sha256
                    ),
                )
            )

        print(
            f"Greenhouse "
            f"{board_token} "
            f"qualifying jobs: "
            f"{len(records)}"
        )

        return records

    async def _extract_lever_site(
        self,
        site: str,
    ) -> list[dict]:

        url = lever_url(site)

        print()
        print(
            f"Fetching Lever site: "
            f"{site}"
        )

        fetched = await self._fetch_source(
            url
        )

        if fetched is None:

            return []

        content, final_url = fetched

        snapshot = store_snapshot(
            content=content,
            source_url=final_url,
            content_type="application/json",
        )

        jobs = json.loads(
            content.decode("utf-8")
        )

        if not isinstance(
            jobs,
            list,
        ):

            return []

        records: list[dict] = []

        for job in jobs:

            if not isinstance(
                job,
                dict,
            ):
                continue

            title = str(
                job.get(
                    "text",
                    "",
                )
            ).strip()

            url = str(
                job.get(
                    "hostedUrl",
                    "",
                )
            ).strip()

            created_raw = (
                job.get("createdAt")
            )

            if isinstance(
                created_raw,
                (int, float),
            ):

                published_at = (
                    datetime.fromtimestamp(
                        created_raw / 1000,
                        tz=timezone.utc,
                    )
                )

            else:

                published_at = (
                    self._parse_datetime(
                        str(
                            created_raw
                            or ""
                        )
                    )
                )

            if (
                not title
                or not url
                or published_at is None
                or not self._is_within_24_hours(
                    published_at
                )
            ):
                continue

            categories = job.get(
                "categories",
                {}
            )

            category = ""

            if isinstance(
                categories,
                dict,
            ):

                category = str(
                    categories.get(
                        "team",
                        ""
                    )
                    or ""
                )

            records.append(
                self._build_record(
                    title=title,
                    url=url,
                    company=site,
                    category=category,
                    published_at=published_at,
                    source_name=(
                        f"Lever:{site}"
                    ),
                    source_url=final_url,
                    snapshot_sha256=(
                        snapshot.sha256
                    ),
                )
            )

        print(
            f"Lever "
            f"{site} "
            f"qualifying jobs: "
            f"{len(records)}"
        )

        return records

    async def extract(
        self,
        limit: int = 20,
    ) -> list[dict]:

        if limit < 1:

            raise ValueError(
                "limit must be >= 1"
            )

        all_records: list[
            dict
        ] = []

        # General job source.
        all_records.extend(
            await self._extract_remotive()
        )

        # Bulk company-board acquisition.
        greenhouse_results = (
            await asyncio.gather(
                *[
                    self._extract_greenhouse_board(
                        board
                    )
                    for board
                    in GREENHOUSE_BOARDS
                ]
            )
        )

        for records in (
            greenhouse_results
        ):

            all_records.extend(
                records
            )

        # Lever boards.
        if LEVER_SITES:

            lever_results = (
                await asyncio.gather(
                    *[
                        self._extract_lever_site(
                            site
                        )
                        for site
                        in LEVER_SITES
                    ]
                )
            )

            for records in (
                lever_results
            ):

                all_records.extend(
                    records
                )

        # Global URL deduplication.
        unique_records: list[
            dict
        ] = []

        seen_urls: set[
            str
        ] = set()

        for record in all_records:

            url = record[
                "url"
            ].strip()

            if (
                not url
                or url in seen_urls
            ):
                continue

            seen_urls.add(
                url
            )

            unique_records.append(
                record
            )

        unique_records.sort(
            key=lambda record: (
                record[
                    "published_at"
                ]
            ),
            reverse=True,
        )

        return unique_records[
            :limit
        ]


async def extract_jobs_to_jsonl(
    limit: int = 20,
) -> list[dict]:

    extractor = JobExtractor()

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

    print()

    print(
        "Jobs dataset written to: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Records written: "
        f"{len(records)}"
    )

    return records