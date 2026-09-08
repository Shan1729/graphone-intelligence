from __future__ import annotations

from graphone.retrieval.base_searcher import (
    DeterministicJSONLSearcher,
)


class ResearchPaperSearcher(
    DeterministicJSONLSearcher,
):
    """
    Deterministic searcher for the GraphOne
    research papers dataset.

    Searches only records already stored in the
    research_papers JSONL export.

    No LLM calls are made.

    No external data is acquired.

    No records are generated or modified.
    """

    DATASET_NAME = (
        "research_papers"
    )

    RECORD_ID_PREFIX = (
        "research_paper"
    )

    SEARCHABLE_FIELDS = (
        "title",
        "authors",
        "paper_url",
        "github_url",
        "source_url",
    )

    FIELD_WEIGHTS = {
        "title": 10,
        "authors": 6,
        "github_url": 4,
        "paper_url": 3,
        "source_url": 1,
    }

    DATASET_STOPWORDS = {
        "paper",
        "papers",
        "research",
        "study",
        "studies",
        "find",
        "show",
        "me",
        "about",
        "the",
        "a",
        "an",
        "latest",
        "recent",
    }

    QUERY_ALIASES = {
        "ai": {
            "ai",
            "artificial intelligence",
        },
        "ml": {
            "ml",
            "machine learning",
        },
        "llm": {
            "llm",
            "language model",
            "language models",
            "large language model",
            "large language models",
        },
        "agent": {
            "agent",
            "agents",
            "agentic",
            "web agent",
            "web agents",
        },
        "agents": {
            "agent",
            "agents",
            "agentic",
            "web agent",
            "web agents",
        },
        "bci": {
            "bci",
            "brain computer interface",
            "brain-computer interface",
            "brain computer interfaces",
            "brain-computer interfaces",
        },
    }

    def _is_valid_record(
        self,
        record: dict,
    ) -> bool:
        """
        Validate the minimum structure required for a
        research paper record.

        Provenance validation is handled separately by
        the base searcher when EvidenceRecord objects
        are created.
        """

        if (
            record.get(
                "record_type"
            )
            != "RESEARCH_PAPER"
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

        authors = record.get(
            "authors"
        )

        if authors is not None and not isinstance(
            authors,
            list,
        ):
            return False

        paper_url = record.get(
            "paper_url"
        )

        if (
            paper_url is not None
            and not isinstance(
                paper_url,
                str,
            )
        ):
            return False

        published_date = record.get(
            "published_date"
        )

        if (
            published_date is not None
            and not isinstance(
                published_date,
                str,
            )
        ):
            return False

        return True