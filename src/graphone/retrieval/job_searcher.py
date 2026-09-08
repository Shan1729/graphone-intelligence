from __future__ import annotations

from graphone.retrieval.base_searcher import (
    DeterministicJSONLSearcher,
)


class JobSearcher(
    DeterministicJSONLSearcher,
):
    """
    Deterministic searcher for the local GraphOne
    jobs dataset.

    No external acquisition occurs during search.

    No LLM calls are made.
    """

    DATASET_NAME = "jobs"

    RECORD_ID_PREFIX = "job"

    SEARCHABLE_FIELDS = (
        "title",
        "company",
        "category",
        "source",
        "url",
    )

    FIELD_WEIGHTS = {
        "title": 10,
        "company": 7,
        "category": 5,
        "source": 3,
        "url": 1,
    }

    DATASET_STOPWORDS = {
        "job",
        "jobs",
        "career",
        "careers",
        "work",
        "role",
        "roles",
        "position",
        "positions",
        "find",
        "show",
        "me",
        "about",
        "the",
        "a",
        "an",
        "and",
        "or",
        "for",
        "with",
    }

    QUERY_ALIASES = {
        "ai": {
            "ai",
            "artificial intelligence",
            "machine learning",
            "machine-learning",
            "ml",
        },
        "artificial intelligence": {
            "artificial intelligence",
            "ai",
        },
        "machine learning": {
            "machine learning",
            "machine-learning",
            "ml",
        },
        "deep learning": {
            "deep learning",
        },
        "ml": {
            "ml",
            "machine learning",
            "machine-learning",
        },
        "data": {
            "data",
            "data scientist",
            "data engineer",
            "data analyst",
            "data science",
            "analytics",
        },
        "data science": {
            "data science",
            "data scientist",
        },
        "data engineering": {
            "data engineering",
            "data engineer",
        },
        "data scientist": {
            "data scientist",
        },
        "data engineer": {
            "data engineer",
        },
        "data analyst": {
            "data analyst",
        },
        "llm": {
            "llm",
            "large language model",
            "large language models",
        },
        "large language model": {
            "large language model",
            "large language models",
            "llm",
        },
        "large language models": {
            "large language model",
            "large language models",
            "llm",
        },
        "generative ai": {
            "generative ai",
            "generative-ai",
            "llm",
        },
        "agent": {
            "agent",
            "agents",
            "agentic",
        },
        "agents": {
            "agent",
            "agents",
            "agentic",
        },
        "developer": {
            "developer",
            "software engineer",
            "software developer",
        },
        "engineer": {
            "engineer",
            "engineering",
        },
    }

    def _is_valid_record(
        self,
        record: dict,
    ) -> bool:
        """
        Validate the minimum structure required for
        a normalized GraphOne job record.
        """

        if (
            record.get(
                "record_type"
            )
            != "JOB"
        ):

            return False

        title = record.get(
            "title"
        )

        if (
            not isinstance(
                title,
                str,
            )
            or not title.strip()
        ):

            return False

        url = record.get(
            "url"
        )

        if (
            not isinstance(
                url,
                str,
            )
            or not url.strip()
        ):

            return False

        return True