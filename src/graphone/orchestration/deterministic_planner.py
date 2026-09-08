from __future__ import annotations

import re

from graphone.orchestration.contracts import (
    OrchestrationPlan,
    SearchRequest,
)
from graphone.orchestration.planner import (
    Planner,
)


class DeterministicPlanner(Planner):
    """
    Deterministic planner for testing the GraphOne
    orchestration pipeline.

    The planner:

    - detects relevant datasets
    - splits multi-part user requests
    - creates dataset-specific search queries
    - does not use an LLM
    - does not generate external data
    """

    DATASET_KEYWORDS = {
        "startups": (
            "startup",
            "startups",
            "company",
            "companies",
            "founder",
            "founders",
        ),
        "products": (
            "product",
            "products",
            "brand",
            "brands",
        ),
        "research_papers": (
            "paper",
            "papers",
            "research",
            "study",
            "studies",
        ),
        "jobs": (
            "job",
            "jobs",
            "hiring",
            "career",
            "careers",
            "position",
            "positions",
            "role",
            "roles",
        ),
        "news": (
            "news",
            "announcement",
            "announcements",
            "latest",
            "recent",
        ),
    }

    async def create_plan(
        self,
        user_query: str,
    ) -> OrchestrationPlan:
        """
        Convert a user query into deterministic,
        dataset-specific search requests.
        """

        normalized_query = " ".join(
            user_query.split()
        )

        if not normalized_query:
            raise ValueError(
                "user_query must not be empty"
            )

        query_parts = (
            self._split_query(
                normalized_query
            )
        )

        dataset_queries: dict[
            str,
            list[str]
        ] = {}

        for part in query_parts:

            detected_datasets = (
                self._detect_datasets(
                    part
                )
            )

            for dataset in detected_datasets:

                dataset_queries.setdefault(
                    dataset,
                    [],
                ).append(
                    part
                )

        # Safe fallback:
        # if no dataset intent is detected,
        # search all available datasets.
        if not dataset_queries:

            for dataset in (
                self.DATASET_KEYWORDS
            ):

                dataset_queries[
                    dataset
                ] = [
                    normalized_query
                ]

        searches: list[
            SearchRequest
        ] = []

        for (
            dataset,
            queries,
        ) in dataset_queries.items():

            dataset_query = (
                self._build_dataset_query(
                    dataset=dataset,
                    queries=queries,
                    full_query=normalized_query,
                )
            )

            searches.append(
                SearchRequest(
                    dataset=dataset,
                    query=dataset_query,
                    limit=20,
                )
            )

        return OrchestrationPlan(
            user_query=normalized_query,
            searches=tuple(
                searches
            ),
        )

    def _split_query(
        self,
        user_query: str,
    ) -> list[str]:
        """
        Split multi-part requests into separate
        candidate search clauses.

        Example:

        Find cybersecurity jobs and scientific
        literacy news

        becomes:

        [
            "Find cybersecurity jobs",
            "scientific literacy news",
        ]
        """

        parts = re.split(
            r"\s+(?:and|also|plus)\s+"
            r"|[,;]",
            user_query,
            flags=re.IGNORECASE,
        )

        cleaned_parts: list[
            str
        ] = []

        for part in parts:

            normalized_part = " ".join(
                part.split()
            )

            if normalized_part:

                cleaned_parts.append(
                    normalized_part
                )

        return (
            cleaned_parts
            or [user_query]
        )

    def _detect_datasets(
        self,
        query_part: str,
    ) -> list[str]:
        """
        Detect which GraphOne datasets are relevant
        to one query clause.
        """

        query_lower = (
            query_part.casefold()
        )

        datasets: list[str] = []

        for (
            dataset,
            keywords,
        ) in (
            self.DATASET_KEYWORDS.items()
        ):

            if any(
                re.search(
                    rf"\b{re.escape(keyword)}\b",
                    query_lower,
                )
                for keyword in keywords
            ):

                datasets.append(
                    dataset
                )

        return datasets

    def _build_dataset_query(
        self,
        dataset: str,
        queries: list[str],
        full_query: str,
    ) -> str:
        """
        Build one deterministic query for a dataset.

        When a dataset has an explicitly matching
        clause, that clause is used.

        This prevents unrelated concepts intended
        for another dataset from being passed into
        deterministic AND-style retrieval.
        """

        cleaned_queries = [
            " ".join(
                query.split()
            )
            for query in queries
            if query.strip()
        ]

        if cleaned_queries:

            return " ".join(
                cleaned_queries
            )

        return full_query