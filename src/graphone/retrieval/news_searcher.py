from __future__ import annotations

from graphone.retrieval.base_searcher import (
    DeterministicJSONLSearcher,
)


class NewsSearcher(
    DeterministicJSONLSearcher,
):
    """
    Deterministic searcher for the local GraphOne
    news dataset.

    Searches only previously acquired records.

    No external acquisition occurs during search.

    No LLM calls are made.
    """

    DATASET_NAME = "news"

    RECORD_ID_PREFIX = "news"

    SEARCHABLE_FIELDS = (
        "title",
        "source",
        "item_type",
        "url",
    )

    FIELD_WEIGHTS = {
        "title": 10,
        "source": 5,
        "item_type": 2,
        "url": 1,
    }

    DATASET_STOPWORDS = {
        "news",
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
        "latest",
        "recent",
    }

    QUERY_ALIASES = {
        "ai": {
            "ai",
            "artificial intelligence",
        },
        "artificial intelligence": {
            "artificial intelligence",
            "ai",
        },
        "digitalisation": {
            "digitalisation",
            "digitalization",
        },
        "digitalization": {
            "digitalization",
            "digitalisation",
        },
        "scientific": {
            "scientific",
            "science",
        },
        "science": {
            "science",
            "scientific",
        },
    }

    def _is_valid_record(
        self,
        record: dict,
    ) -> bool:
        """
        Validate the minimum structure required for
        a normalized GraphOne news record.
        """

        if (
            record.get(
                "record_type"
            )
            != "NEWS"
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