from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote
import xml.etree.ElementTree as ET

import httpx


ARXIV_API_URL = "https://export.arxiv.org/api/query"

ARXIV_ATOM_NAMESPACE = {
    "atom": "http://www.w3.org/2005/Atom",
}


@dataclass(frozen=True)
class ResearchPaper:
    schema_version: str
    record_type: str
    title: str
    authors: list[str]
    paper_url: str
    github_url: str | None
    github_stars: int | None
    published_date: str
    source_url: str


class ArxivBulkExtractor:
    """
    Bulk extractor for real research-paper metadata from arXiv.

    Uses pagination so the same extraction logic can scale from
    small batches to large one-time extraction workloads.
    """

    def __init__(
        self,
        batch_size: int = 100,
        timeout: float = 30.0,
        max_retries: int = 4,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")

        self.batch_size = batch_size
        self.timeout = timeout
        self.max_retries = max_retries

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        search_query: str,
        start: int,
        max_results: int,
    ) -> str:
        """
        Fetch one paginated arXiv API response with retry handling.
        """

        params = {
            "search_query": search_query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.get(
                    ARXIV_API_URL,
                    params=params,
                )

                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)
                        continue

                response.raise_for_status()

                return response.text

            except Exception as exc:
                last_error = exc

                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)

        raise RuntimeError(
            f"Failed to fetch arXiv page starting at {start}: {last_error}"
        )

    def _parse_entries(
        self,
        xml_content: str,
    ) -> list[ResearchPaper]:
        """
        Parse real arXiv Atom feed entries into structured records.
        """

        root = ET.fromstring(xml_content)

        papers: list[ResearchPaper] = []

        entries = root.findall(
            "atom:entry",
            ARXIV_ATOM_NAMESPACE,
        )

        for entry in entries:
            title_element = entry.find(
                "atom:title",
                ARXIV_ATOM_NAMESPACE,
            )

            id_element = entry.find(
                "atom:id",
                ARXIV_ATOM_NAMESPACE,
            )

            published_element = entry.find(
                "atom:published",
                ARXIV_ATOM_NAMESPACE,
            )

            if (
                title_element is None
                or id_element is None
                or published_element is None
            ):
                continue

            title = " ".join(
                title_element.text.strip().split()
            )

            paper_url = id_element.text.strip()

            authors = []

            for author in entry.findall(
                "atom:author",
                ARXIV_ATOM_NAMESPACE,
            ):
                name_element = author.find(
                    "atom:name",
                    ARXIV_ATOM_NAMESPACE,
                )

                if (
                    name_element is not None
                    and name_element.text
                ):
                    authors.append(
                        name_element.text.strip()
                    )

            published_raw = published_element.text.strip()

            published_date = (
                datetime.fromisoformat(
                    published_raw.replace("Z", "+00:00")
                )
                .astimezone(timezone.utc)
                .isoformat()
            )

            papers.append(
                ResearchPaper(
                    schema_version="1.0",
                    record_type="RESEARCH_PAPER",
                    title=title,
                    authors=authors,
                    paper_url=paper_url,
                    github_url=None,
                    github_stars=None,
                    published_date=published_date,
                    source_url=paper_url,
                )
            )

        return papers

    async def extract(
        self,
        target_count: int = 1000,
        search_query: str = (
            "cat:cs.AI OR cat:cs.LG OR cat:cs.CL"
        ),
    ) -> list[ResearchPaper]:
        """
        Extract real research papers until target_count is reached.
        """

        if target_count < 1:
            raise ValueError(
                "target_count must be >= 1"
            )

        papers: list[ResearchPaper] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:

            start = 0

            while len(papers) < target_count:

                remaining = (
                    target_count - len(papers)
                )

                page_size = min(
                    self.batch_size,
                    remaining,
                )

                xml_content = await self._fetch_page(
                    client=client,
                    search_query=search_query,
                    start=start,
                    max_results=page_size,
                )

                page_papers = self._parse_entries(
                    xml_content
                )

                if not page_papers:
                    break

                for paper in page_papers:
                    if (
                        paper.paper_url
                        not in seen_urls
                    ):
                        papers.append(paper)

                        seen_urls.add(
                            paper.paper_url
                        )

                    if (
                        len(papers)
                        >= target_count
                    ):
                        break

                start += page_size

                # Respectful pacing for the upstream API.
                await asyncio.sleep(1.0)

        return papers[:target_count]