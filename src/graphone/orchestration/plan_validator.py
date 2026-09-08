from __future__ import annotations

from graphone.orchestration.contracts import (
    OrchestrationPlan,
    SearchRequest,
)


ALLOWED_DATASETS = {
    "startups",
    "products",
    "research_papers",
    "jobs",
    "news",
}


class PlanValidator:
    """
    Deterministically validates an orchestration plan.

    The planner may propose searches, but this validator
    ensures that only valid and relevant searches are
    allowed to reach the DatasetRouter.
    """

    def validate(
        self,
        plan: OrchestrationPlan,
    ) -> OrchestrationPlan:

        normalized_query = " ".join(
            plan.user_query.split()
        )

        if not normalized_query:

            raise ValueError(
                "plan user_query must not be empty"
            )

        query_lower = (
            normalized_query.casefold()
        )

        allowed_for_query = (
            self._detect_relevant_datasets(
                query_lower
            )
        )

        validated_searches: list[
            SearchRequest
        ] = []

        seen_datasets: set[
            str
        ] = set()

        for search in plan.searches:

            if (
                search.dataset
                not in ALLOWED_DATASETS
            ):
                raise ValueError(
                    "Plan contains invalid dataset: "
                    f"{search.dataset}"
                )

            if (
                search.dataset
                not in allowed_for_query
            ):
                continue

            if (
                search.dataset
                in seen_datasets
            ):
                continue

            normalized_search_query = (
                " ".join(
                    search.query.split()
                )
            )

            if not normalized_search_query:

                continue

            if (
                not isinstance(
                    search.limit,
                    int,
                )
                or isinstance(
                    search.limit,
                    bool,
                )
                or search.limit < 1
                or search.limit > 50
            ):
                raise ValueError(
                    "Search limit must be an integer "
                    "between 1 and 50"
                )

            seen_datasets.add(
                search.dataset
            )

            validated_searches.append(
                SearchRequest(
                    dataset=search.dataset,
                    query=normalized_search_query,
                    limit=search.limit,
                )
            )

        if not validated_searches:

            raise ValueError(
                "No relevant searches remain after "
                "plan validation"
            )

        return OrchestrationPlan(
            user_query=normalized_query,
            searches=tuple(
                validated_searches
            ),
        )

    def _detect_relevant_datasets(
        self,
        query_lower: str,
    ) -> set[str]:

        datasets: set[str] = set()

        if any(
            keyword in query_lower
            for keyword in (
                "startup",
                "startups",
                "company",
                "companies",
                "founder",
                "founders",
            )
        ):
            datasets.add(
                "startups"
            )

        if any(
            keyword in query_lower
            for keyword in (
                "product",
                "products",
                "brand",
                "brands",
            )
        ):
            datasets.add(
                "products"
            )

        if any(
            keyword in query_lower
            for keyword in (
                "paper",
                "papers",
                "research",
                "study",
                "studies",
            )
        ):
            datasets.add(
                "research_papers"
            )

        if any(
            keyword in query_lower
            for keyword in (
                "job",
                "jobs",
                "hiring",
                "career",
                "careers",
                "vacancy",
                "vacancies",
            )
        ):
            datasets.add(
                "jobs"
            )

        if any(
            keyword in query_lower
            for keyword in (
                "news",
                "announcement",
                "announcements",
                "latest",
                "recent",
                "update",
                "updates",
            )
        ):
            datasets.add(
                "news"
            )

        return datasets