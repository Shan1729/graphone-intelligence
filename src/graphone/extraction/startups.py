from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

from graphone.acquisition.cas import store_snapshot
from graphone.storage.db import init_db, record_acquisition


YC_COMPANIES_URL = "https://yc-oss.github.io/api/companies/all.json"


@dataclass(frozen=True)
class Startup:
    schema_version: str
    record_type: str
    source_name: str
    source_url: str
    entity_name: str
    employee_count: int | None
    company_url: str | None
    website: str | None
    description: str | None
    industry: str | None
    location: str | None
    raw_snapshot_sha256: str
    collected_at: str


class YCStartupExtractor:
    """
    Deterministic bulk extractor for startup records.

    Records are parsed directly from the YC public dataset.
    No LLM is used to generate, infer, guess, or complete entity data.
    """

    def __init__(
        self,
        timeout: float = 60.0,
        max_retries: int = 4,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries

    async def _fetch_dataset(self) -> tuple[bytes, str]:
        """
        Fetch the complete YC company dataset with retry handling.
        """

        last_error: Exception | None = None

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:

            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.get(
                        YC_COMPANIES_URL
                    )

                    if (
                        response.status_code == 429
                        or response.status_code >= 500
                    ):
                        if attempt < self.max_retries:
                            await asyncio.sleep(
                                2 ** attempt
                            )
                            continue

                    response.raise_for_status()

                    return (
                        response.content,
                        str(response.url),
                    )

                except Exception as exc:
                    last_error = exc

                    if attempt < self.max_retries:
                        await asyncio.sleep(
                            2 ** attempt
                        )

        raise RuntimeError(
            "Failed to fetch YC company dataset: "
            f"{last_error}"
        )

    @staticmethod
    def _normalize_text(
        value: object,
    ) -> str | None:
        """
        Deterministically normalize text without generating content.
        """

        if not isinstance(value, str):
            return None

        value = " ".join(
            value.split()
        )

        return value or None

    @staticmethod
    def _normalize_url(
        value: object,
    ) -> str | None:
        """
        Accept only syntactically valid HTTP/HTTPS URLs.

        No URL is generated, guessed, or completed.
        The source value is retained only if it is already
        a valid absolute web URL.
        """

        if not isinstance(value, str):
            return None

        value = value.strip()

        if not value:
            return None

        try:
            parsed = urlsplit(value)
        except ValueError:
            return None

        if parsed.scheme not in {
            "http",
            "https",
        }:
            return None

        if not parsed.netloc:
            return None

        if not parsed.hostname:
            return None

        return value

    @staticmethod
    def _extract_employee_count(
        record: dict,
    ) -> int | None:
        """
        Read employee count only when explicitly represented
        as a valid integer in the source record.
        """

        possible_fields = (
            "team_size",
            "employee_count",
            "employees",
        )

        for field in possible_fields:
            value = record.get(field)

            if (
                isinstance(value, int)
                and value >= 0
            ):
                return value

            if (
                isinstance(value, str)
                and value.isdigit()
            ):
                return int(value)

        return None

    def _parse_records(
        self,
        dataset: object,
        source_url: str,
        snapshot_sha256: str,
        collected_at: str,
    ) -> list[Startup]:
        """
        Parse only actual source records.

        Records missing required valid source values
        are skipped rather than fabricated or completed.
        """

        if not isinstance(dataset, list):
            raise ValueError(
                "YC dataset must be a JSON list"
            )

        startups: list[Startup] = []
        seen_names: set[str] = set()

        for raw_record in dataset:
            if not isinstance(
                raw_record,
                dict,
            ):
                continue

            entity_name = self._normalize_text(
                raw_record.get("name")
            )

            if not entity_name:
                continue

            website = self._normalize_url(
                raw_record.get("website")
            )

            # Do not invent or repair websites.
            # Skip records whose source website is absent
            # or not a valid absolute HTTP/HTTPS URL.
            if website is None:
                continue

            dedupe_key = (
                entity_name.casefold()
            )

            if dedupe_key in seen_names:
                continue

            company_url = self._normalize_text(
                raw_record.get("url")
            )

            description = self._normalize_text(
                raw_record.get("one_liner")
            )

            if description is None:
                description = (
                    self._normalize_text(
                        raw_record.get(
                            "long_description"
                        )
                    )
                )

            industry = self._normalize_text(
                raw_record.get("industry")
            )

            location = self._normalize_text(
                raw_record.get("all_locations")
            )

            startups.append(
                Startup(
                    schema_version="1.0",
                    record_type="STARTUP",
                    source_name="Y Combinator",
                    source_url=source_url,
                    entity_name=entity_name,
                    employee_count=(
                        self._extract_employee_count(
                            raw_record
                        )
                    ),
                    company_url=company_url,
                    website=website,
                    description=description,
                    industry=industry,
                    location=location,
                    raw_snapshot_sha256=(
                        snapshot_sha256
                    ),
                    collected_at=collected_at,
                )
            )

            seen_names.add(
                dedupe_key
            )

        return startups

    async def extract(
        self,
        target_count: int = 1000,
    ) -> list[Startup]:
        """
        Extract up to target_count unique real startup records.
        """

        if target_count < 1:
            raise ValueError(
                "target_count must be >= 1"
            )

        init_db()

        content, final_url = (
            await self._fetch_dataset()
        )

        snapshot = store_snapshot(
            content=content,
            source_url=final_url,
            content_type="application/json",
        )

        collected_at = datetime.now(
            timezone.utc
        ).isoformat()

        record_acquisition(
            sha256=snapshot.sha256,
            source_url=final_url,
            created_at=collected_at,
        )

        dataset = json.loads(
            content.decode("utf-8")
        )

        startups = self._parse_records(
            dataset=dataset,
            source_url=final_url,
            snapshot_sha256=snapshot.sha256,
            collected_at=collected_at,
        )

        return startups[:target_count]