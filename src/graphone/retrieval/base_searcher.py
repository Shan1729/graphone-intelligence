from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

from graphone.orchestration.contracts import (
    EvidenceRecord,
    SearchRequest,
)
from graphone.orchestration.router import (
    DatasetSearcher,
)


class DeterministicJSONLSearcher(
    DatasetSearcher,
    ABC,
):
    """
    Reusable deterministic search engine for JSONL datasets.

    Features:

    - JSONL reading
    - JSON parsing
    - deterministic text normalization
    - tokenization
    - dataset stopword removal
    - multi-word query concept handling
    - query aliases
    - exact token matching
    - deterministic phrase matching
    - weighted scoring
    - provenance validation
    - evidence record creation
    - stable ranking

    No LLM calls are made.

    No semantic inference or source-data generation
    occurs during retrieval.
    """

    DATASET_NAME: str

    RECORD_ID_PREFIX: str

    SEARCHABLE_FIELDS: tuple[str, ...]

    FIELD_WEIGHTS: dict[str, int]

    DATASET_STOPWORDS: set[str] = set()

    QUERY_ALIASES: dict[
        str,
        set[str],
    ] = {}

    def __init__(
        self,
        file_path: Path | str,
    ) -> None:

        self.file_path = Path(
            file_path
        )

        if not self.file_path.exists():

            raise FileNotFoundError(
                "Dataset file not found: "
                f"{self.file_path}"
            )

    @staticmethod
    def _normalize_text(
        value: object,
    ) -> str:
        """
        Normalize text deterministically.

        No semantic generation or inference occurs.
        """

        if not isinstance(
            value,
            str,
        ):
            return ""

        return " ".join(
            value.casefold().split()
        )

    @classmethod
    def _tokenize(
        cls,
        value: object,
    ) -> set[str]:
        """
        Convert text into deterministic tokens.
        """

        normalized = (
            cls._normalize_text(
                value
            )
        )

        return set(
            re.findall(
                r"[a-z0-9]+",
                normalized,
            )
        )

    def _query_terms(
        self,
        query: str,
    ) -> list[set[str]]:
        """
        Convert a query into deterministic concept groups.

        Recognized multi-word concepts are preserved as
        one concept instead of being split into separate
        AND requirements.

        Example:

            Find AI and machine learning jobs

        becomes approximately:

            {ai aliases}
            {machine learning aliases}

        rather than:

            AI
            machine
            learning

        This remains deterministic and does not perform
        semantic inference.
        """

        normalized_query = (
            self._normalize_text(
                query
            )
        )

        if not normalized_query:
            return []

        multi_word_concepts = (
            "artificial intelligence",
            "machine learning",
            "machine-learning",
            "deep learning",
            "data science",
            "data engineering",
            "data scientist",
            "data engineer",
            "data analyst",
            "large language model",
            "large language models",
            "generative ai",
            "computer vision",
            "natural language processing",
        )

        terms: list[
            set[str]
        ] = []

        consumed_tokens: set[
            str
        ] = set()

        for concept in (
            multi_word_concepts
        ):

            normalized_concept = (
                self._normalize_text(
                    concept
                )
            )

            if (
                normalized_concept
                not in normalized_query
            ):
                continue

            concept_tokens = (
                self._tokenize(
                    normalized_concept
                )
            )

            consumed_tokens.update(
                concept_tokens
            )

            aliases = (
                self.QUERY_ALIASES.get(
                    normalized_concept
                )
            )

            if aliases:

                normalized_aliases = {

                    self._normalize_text(
                        alias
                    )

                    for alias in aliases

                    if self._normalize_text(
                        alias
                    )
                }

                if normalized_aliases:

                    terms.append(
                        normalized_aliases
                    )

                    continue

            terms.append(
                {
                    normalized_concept
                }
            )

        query_tokens = (
            self._tokenize(
                normalized_query
            )
        )

        query_tokens -= (
            self.DATASET_STOPWORDS
        )

        query_tokens -= (
            consumed_tokens
        )

        for token in sorted(
            query_tokens
        ):

            aliases = (
                self.QUERY_ALIASES.get(
                    token
                )
            )

            if aliases:

                normalized_aliases = {

                    self._normalize_text(
                        alias
                    )

                    for alias in aliases

                    if self._normalize_text(
                        alias
                    )
                }

                if normalized_aliases:

                    terms.append(
                        normalized_aliases
                    )

            else:

                terms.append(
                    {token}
                )

        return terms

    def _term_matches_field(
        self,
        alternatives: set[str],
        field_text: str,
        field_tokens: set[str],
    ) -> bool:
        """
        Check whether one deterministic alternative
        matches a searchable field.

        Single-word alternatives require exact token
        matching.

        Multi-word alternatives require deterministic
        phrase matching.
        """

        for alternative in alternatives:

            normalized_alternative = (
                self._normalize_text(
                    alternative
                )
            )

            if not normalized_alternative:

                continue

            if (
                " "
                in normalized_alternative
            ):

                if (
                    normalized_alternative
                    in field_text
                ):

                    return True

            elif (
                normalized_alternative
                in field_tokens
            ):

                return True

        return False

    def _score_record(
        self,
        record: dict,
        query: str,
    ) -> int:
        """
        Deterministically score one record.

        Every required query concept must match at least
        one searchable field.

        If any required concept is missing, the record
        receives score 0.
        """

        query_terms = (
            self._query_terms(
                query
            )
        )

        if not query_terms:

            return 0

        field_data: dict[
            str,
            tuple[
                str,
                set[str],
            ],
        ] = {}

        for field in (
            self.SEARCHABLE_FIELDS
        ):

            field_text = (
                self._normalize_text(
                    record.get(
                        field
                    )
                )
            )

            field_tokens = (
                self._tokenize(
                    field_text
                )
            )

            field_data[field] = (
                field_text,
                field_tokens,
            )

        total_score = 0

        for alternatives in (
            query_terms
        ):

            matched = False

            best_weight = 0

            for (
                field,
                (
                    field_text,
                    field_tokens,
                ),
            ) in field_data.items():

                if (
                    self._term_matches_field(
                        alternatives=alternatives,
                        field_text=field_text,
                        field_tokens=field_tokens,
                    )
                ):

                    matched = True

                    best_weight = max(
                        best_weight,
                        self.FIELD_WEIGHTS.get(
                            field,
                            1,
                        ),
                    )

            if not matched:

                return 0

            total_score += (
                best_weight
            )

        return total_score

    def _create_evidence_record(
        self,
        record: dict,
        line_number: int,
    ) -> EvidenceRecord | None:
        """
        Create evidence only when required provenance
        information exists.
        """

        source_url = record.get(
            "source_url"
        )

        snapshot_sha256 = record.get(
            "raw_snapshot_sha256"
        )

        if (
            not isinstance(
                source_url,
                str,
            )
            or not source_url.strip()
        ):

            return None

        if (
            not isinstance(
                snapshot_sha256,
                str,
            )
            or not snapshot_sha256.strip()
        ):

            return None

        return EvidenceRecord(
            dataset=self.DATASET_NAME,
            record_id=(
                f"{self.RECORD_ID_PREFIX}:"
                f"{line_number}"
            ),
            payload=record,
            source_url=source_url,
            raw_snapshot_sha256=(
                snapshot_sha256
            ),
        )

    @abstractmethod
    def _is_valid_record(
        self,
        record: dict,
    ) -> bool:
        """
        Dataset-specific structural validation.

        Each concrete searcher must implement this.
        """

    async def search(
        self,
        request: SearchRequest,
    ) -> list[EvidenceRecord]:
        """
        Search the local JSONL dataset deterministically.

        Ranking:

        1. Descending deterministic relevance score.
        2. Ascending source line number for stable ties.
        """

        if (
            request.dataset
            != self.DATASET_NAME
        ):

            raise ValueError(
                f"{self.__class__.__name__} "
                f"can only search dataset "
                f"'{self.DATASET_NAME}'"
            )

        if request.limit < 1:

            return []

        query_terms = (
            self._query_terms(
                request.query
            )
        )

        if not query_terms:

            return []

        scored_results: list[
            tuple[
                int,
                int,
                EvidenceRecord,
            ]
        ] = []

        with self.file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for (
                line_number,
                line,
            ) in enumerate(
                file,
                start=1,
            ):

                line = line.strip()

                if not line:

                    continue

                try:

                    record = json.loads(
                        line
                    )

                except json.JSONDecodeError:

                    continue

                if not isinstance(
                    record,
                    dict,
                ):

                    continue

                if not self._is_valid_record(
                    record
                ):

                    continue

                score = (
                    self._score_record(
                        record=record,
                        query=request.query,
                    )
                )

                if score <= 0:

                    continue

                evidence = (
                    self._create_evidence_record(
                        record=record,
                        line_number=line_number,
                    )
                )

                if evidence is None:

                    continue

                scored_results.append(
                    (
                        score,
                        line_number,
                        evidence,
                    )
                )

        scored_results.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        return [
            evidence
            for (
                _,
                _,
                evidence,
            )
            in scored_results[
                :request.limit
            ]
        ]