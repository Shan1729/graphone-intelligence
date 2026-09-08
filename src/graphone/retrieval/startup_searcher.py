from __future__ import annotations

import json
import re
from pathlib import Path

from graphone.orchestration.contracts import (
    EvidenceRecord,
    SearchRequest,
)
from graphone.orchestration.router import (
    DatasetSearcher,
)


class StartupSearcher(DatasetSearcher):
    """
    Deterministic search adapter for real GraphOne
    startup records.

    Guarantees:

    - Reads only existing acquired records.
    - Does not call an LLM.
    - Does not generate or complete source data.
    - Uses deterministic query expansion only.
    - Removes dataset-context words deterministically.
    - Preserves original payload and provenance.
    """

    SEARCHABLE_FIELDS = (
        "entity_name",
        "description",
        "industry",
        "location",
        "source_name",
        "website",
    )

    FIELD_WEIGHTS = {
        "entity_name": 8,
        "industry": 6,
        "description": 5,
        "location": 3,
        "source_name": 1,
        "website": 1,
    }

    # These words describe the dataset itself.
    #
    # They should not be required to exist inside
    # every individual startup record.
    DATASET_STOPWORDS = {
        "startup",
        "startups",
        "company",
        "companies",
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

    # Explicit deterministic aliases.
    #
    # These are retrieval rules only.
    # They do not generate or infer source records.
    QUERY_ALIASES = {
        "ai": {
            "ai",
            "artificial intelligence",
        },
        "ml": {
            "ml",
            "machine learning",
        },
        "saas": {
            "saas",
            "software as a service",
        },
        "b2b": {
            "b2b",
            "business to business",
        },
        "b2c": {
            "b2c",
            "business to consumer",
        },
    }

    def __init__(
        self,
        file_path: Path | str,
    ) -> None:

        self.file_path = Path(
            file_path
        )

        if not self.file_path.exists():

            raise FileNotFoundError(
                "Startup data file not found: "
                f"{self.file_path}"
            )

    @staticmethod
    def _normalize_text(
        value: object,
    ) -> str:
        """
        Deterministically normalize text.

        No content is generated or inferred.
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

        normalized = cls._normalize_text(
            value
        )

        return set(
            re.findall(
                r"[a-z0-9]+",
                normalized,
            )
        )

    @classmethod
    def _field_text(
        cls,
        record: dict,
        field: str,
    ) -> str:
        """
        Return normalized text for one source field.
        """

        return cls._normalize_text(
            record.get(field)
        )

    def _query_terms(
        self,
        query: str,
    ) -> list[set[str]]:
        """
        Convert a retrieval query into deterministic
        searchable concepts.

        Dataset-context words are removed because
        the dataset itself already guarantees the
        record type.
        """

        query_tokens = self._tokenize(
            query
        )

        query_tokens -= (
            self.DATASET_STOPWORDS
        )

        terms: list[set[str]] = []

        for token in sorted(
            query_tokens
        ):

            aliases = self.QUERY_ALIASES.get(
                token
            )

            if aliases:

                terms.append(
                    set(aliases)
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
        Check deterministic exact matches.

        Single-word alternatives require an exact
        whole-token match.

        Multi-word alternatives require an exact
        normalized phrase match.
        """

        for alternative in alternatives:

            normalized_alternative = (
                self._normalize_text(
                    alternative
                )
            )

            if not normalized_alternative:

                continue

            if " " in normalized_alternative:

                if (
                    normalized_alternative
                    in field_text
                ):
                    return True

            else:

                if (
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
        Calculate deterministic relevance.

        Every meaningful query concept must match
        somewhere in the record.

        Higher-weight fields increase ranking.
        """

        query_terms = self._query_terms(
            query
        )

        if not query_terms:

            return 0

        field_data: dict[
            str,
            tuple[str, set[str]],
        ] = {}

        for field in self.SEARCHABLE_FIELDS:

            field_text = self._field_text(
                record,
                field,
            )

            field_tokens = self._tokenize(
                field_text
            )

            field_data[field] = (
                field_text,
                field_tokens,
            )

        total_score = 0

        for alternatives in query_terms:

            matched = False
            best_weight = 0

            for field, (
                field_text,
                field_tokens,
            ) in field_data.items():

                if self._term_matches_field(
                    alternatives=alternatives,
                    field_text=field_text,
                    field_tokens=field_tokens,
                ):

                    matched = True

                    best_weight = max(
                        best_weight,
                        self.FIELD_WEIGHTS[
                            field
                        ],
                    )

            if not matched:

                return 0

            total_score += best_weight

        return total_score

    def _create_evidence_record(
        self,
        record: dict,
        line_number: int,
    ) -> EvidenceRecord | None:
        """
        Convert a real stored startup record into
        provenance-preserving evidence.

        Records without required provenance are rejected.
        """

        if (
            record.get(
                "record_type"
            )
            != "STARTUP"
        ):

            return None

        entity_name = record.get(
            "entity_name"
        )

        if (
            not isinstance(
                entity_name,
                str,
            )
            or not entity_name.strip()
        ):

            return None

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
            dataset="startups",
            record_id=(
                f"startup:{line_number}"
            ),
            payload=record,
            source_url=source_url,
            raw_snapshot_sha256=(
                snapshot_sha256
            ),
        )

    async def search(
        self,
        request: SearchRequest,
    ) -> list[EvidenceRecord]:
        """
        Search existing real startup records.

        Pipeline:

        1. Read stored JSONL records.
        2. Remove dataset-context terms.
        3. Apply deterministic aliases.
        4. Perform exact token/phrase matching.
        5. Require all meaningful concepts.
        6. Score deterministically.
        7. Rank deterministically.
        8. Preserve provenance.
        """

        if request.dataset != "startups":

            raise ValueError(
                "StartupSearcher can only search "
                "the startups dataset"
            )

        query_terms = self._query_terms(
            request.query
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

            for line_number, line in enumerate(
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

                if (
                    record.get(
                        "record_type"
                    )
                    != "STARTUP"
                ):

                    continue

                score = self._score_record(
                    record=record,
                    query=request.query,
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
            for _, _, evidence
            in scored_results[
                :request.limit
            ]
        ]