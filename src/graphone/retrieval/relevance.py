from __future__ import annotations

import re
from typing import Any


class RelevanceRanker:
    """
    Lightweight deterministic relevance ranker.

    Scores retrieved records against the search query
    before they are passed to the grounded responder.

    No LLM and no external knowledge are used.
    """

    MIN_SCORE = 1

    def filter_and_rank(
        self,
        query: str,
        records: list[Any],
        limit: int,
    ) -> list[Any]:

        query_terms = self._tokenize(
            query
        )

        if not query_terms:
            return records[:limit]

        scored_records: list[
            tuple[int, Any]
        ] = []

        for record in records:

            score = self._score_record(
                query_terms=query_terms,
                record=record,
            )

            if score >= self.MIN_SCORE:

                scored_records.append(
                    (
                        score,
                        record,
                    )
                )

        scored_records.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            record
            for _score, record
            in scored_records[:limit]
        ]

    def _score_record(
        self,
        query_terms: set[str],
        record: Any,
    ) -> int:

        payload = getattr(
            record,
            "payload",
            {},
        )

        if not isinstance(
            payload,
            dict,
        ):
            return 0

        searchable_text = self._build_text(
            payload
        )

        record_terms = self._tokenize(
            searchable_text
        )

        overlap = (
            query_terms
            & record_terms
        )

        return len(
            overlap
        )

    def _build_text(
        self,
        payload: dict[str, Any],
    ) -> str:

        values: list[str] = []

        for value in payload.values():

            if isinstance(
                value,
                str,
            ):

                values.append(
                    value
                )

            elif isinstance(
                value,
                (int, float),
            ):

                values.append(
                    str(value)
                )

            elif isinstance(
                value,
                list,
            ):

                values.extend(
                    str(item)
                    for item in value
                )

        return " ".join(
            values
        )

    def _tokenize(
        self,
        text: str,
    ) -> set[str]:

        tokens = re.findall(
            r"[a-z0-9]+",
            text.casefold(),
        )

        return set(
            tokens
        )