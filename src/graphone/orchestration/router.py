from __future__ import annotations

from abc import ABC, abstractmethod

from graphone.orchestration.contracts import (
    EvidenceRecord,
    OrchestrationPlan,
    SearchRequest,
)


class DatasetSearcher(ABC):
    """
    Controlled interface for searching one GraphOne dataset.

    Searchers must return only real records already
    acquired by GraphOne.

    Searchers must never generate, infer, or fabricate
    external records.
    """

    @abstractmethod
    async def search(
        self,
        request: SearchRequest,
    ) -> list[EvidenceRecord]:
        raise NotImplementedError


class DatasetRouter:
    """
    Deterministic router between an orchestration plan
    and registered dataset search tools.

    The router does not use an LLM.

    It only executes validated search requests against
    explicitly registered searchers.

    Duplicate evidence records are removed
    deterministically.
    """

    def __init__(
        self,
        searchers: dict[str, DatasetSearcher],
    ) -> None:
        self.searchers = dict(searchers)

    async def execute(
        self,
        plan: OrchestrationPlan,
    ) -> tuple[EvidenceRecord, ...]:
        """
        Execute every search request in the plan.

        Only datasets with registered searchers can be
        executed.

        Every returned record is verified to belong to
        the requested dataset.

        Duplicate evidence records are removed using
        their dataset and record ID.
        """

        evidence: list[EvidenceRecord] = []

        seen_records: set[
            tuple[str, str]
        ] = set()

        for request in plan.searches:

            searcher = self.searchers.get(
                request.dataset
            )

            if searcher is None:

                raise ValueError(
                    "No registered searcher for "
                    f"dataset: {request.dataset}"
                )

            results = await searcher.search(
                request
            )

            for record in results:

                if (
                    record.dataset
                    != request.dataset
                ):

                    raise ValueError(
                        "Searcher returned evidence "
                        "for the wrong dataset"
                    )

                record_key = (
                    record.dataset,
                    record.record_id,
                )

                if record_key in seen_records:
                    continue

                seen_records.add(
                    record_key
                )

                evidence.append(
                    record
                )

        return tuple(
            evidence
        )