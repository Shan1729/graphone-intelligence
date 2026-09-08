from __future__ import annotations

import re

from graphone.orchestration.contracts import (
    EvidenceRecord,
)


class EvidenceRanker:
    """
    Deterministically ranks retrieved evidence records
    according to their relevance to the user query.

    No LLM is used.

    Ranking is based on normalized query-term matching
    against the searchable content already contained in
    each EvidenceRecord.
    """

    def rank(
        self,
        user_query: str,
        evidence: tuple[
            EvidenceRecord,
            ...
        ],
        limit: int = 20,
    ) -> tuple[
        EvidenceRecord,
        ...
    ]:
        """
        Rank evidence by deterministic relevance score.

        Records with stronger query-term matches are
        returned first.

        The original EvidenceRecord objects are returned
        unchanged.
        """

        normalized_query = (
            self._normalize_text(
                user_query
            )
        )

        if not normalized_query:

            raise ValueError(
                "user_query must not be empty"
            )

        if (
            not isinstance(
                limit,
                int,
            )
            or isinstance(
                limit,
                bool,
            )
            or limit < 1
        ):
            raise ValueError(
                "limit must be a positive integer"
            )

        if not evidence:

            return ()

        query_tokens = (
            self._tokenize(
                normalized_query
            )
        )

        scored_records: list[
            tuple[
                int,
                int,
                EvidenceRecord,
            ]
        ] = []

        for (
            index,
            record,
        ) in enumerate(
            evidence
        ):

            score = (
                self._score_record(
                    query_tokens=query_tokens,
                    record=record,
                )
            )

            scored_records.append(
                (
                    score,
                    index,
                    record,
                )
            )

        scored_records.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        ranked_records = tuple(
            record
            for (
                _,
                _,
                record,
            ) in scored_records[
                :limit
            ]
        )

        return ranked_records

    def _score_record(
        self,
        query_tokens: tuple[
            str,
            ...
        ],
        record: EvidenceRecord,
    ) -> int:
        """
        Calculate a deterministic relevance score.

        Higher-value fields receive stronger weights.
        """

        payload = record.payload

        score = 0

        title_text = (
            self._normalize_text(
                str(
                    payload.get(
                        "title",
                        "",
                    )
                )
            )
        )

        name_text = (
            self._normalize_text(
                str(
                    payload.get(
                        "name",
                        "",
                    )
                )
            )
        )

        description_text = (
            self._normalize_text(
                str(
                    payload.get(
                        "description",
                        "",
                    )
                )
            )
        )

        summary_text = (
            self._normalize_text(
                str(
                    payload.get(
                        "summary",
                        "",
                    )
                )
            )
        )

        abstract_text = (
            self._normalize_text(
                str(
                    payload.get(
                        "abstract",
                        "",
                    )
                )
            )
        )

        content_text = (
            self._normalize_text(
                str(
                    payload
                )
            )
        )

        title_tokens = set(
            self._tokenize(
                title_text
            )
        )

        name_tokens = set(
            self._tokenize(
                name_text
            )
        )

        description_tokens = set(
            self._tokenize(
                description_text
            )
        )

        summary_tokens = set(
            self._tokenize(
                summary_text
            )
        )

        abstract_tokens = set(
            self._tokenize(
                abstract_text
            )
        )

        content_tokens = set(
            self._tokenize(
                content_text
            )
        )

        for token in query_tokens:

            if token in title_tokens:

                score += 10

            if token in name_tokens:

                score += 10

            if token in description_tokens:

                score += 5

            if token in summary_tokens:

                score += 5

            if token in abstract_tokens:

                score += 5

            if token in content_tokens:

                score += 1

        return score

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        """
        Normalize text for deterministic comparison.
        """

        normalized = (
            value.casefold()
        )

        normalized = (
            re.sub(
                r"\s+",
                " ",
                normalized,
            )
        )

        return normalized.strip()

    @staticmethod
    def _tokenize(
        value: str,
    ) -> tuple[
        str,
        ...
    ]:
        """
        Extract alphanumeric tokens.

        Duplicate tokens are removed while preserving
        their original order.
        """

        tokens = re.findall(
            r"[a-z0-9]+",
            value.casefold(),
        )

        unique_tokens: list[
            str
        ] = []

        seen: set[
            str
        ] = set()

        for token in tokens:

            if token in seen:

                continue

            seen.add(
                token
            )

            unique_tokens.append(
                token
            )

        return tuple(
            unique_tokens
        )