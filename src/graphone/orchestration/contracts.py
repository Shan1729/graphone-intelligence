from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


DatasetName = Literal[
    "startups",
    "products",
    "research_papers",
    "jobs",
    "news",
]


@dataclass(frozen=True)
class SearchRequest:
    """
    A deterministic search request produced by the
    orchestration layer.

    This object does not contain generated external data.
    It only describes what existing datasets should be
    searched.
    """

    dataset: DatasetName
    query: str
    limit: int


@dataclass(frozen=True)
class OrchestrationPlan:
    """
    Structured execution plan for a user request.

    The plan determines which real datasets should be
    searched. It must not contain invented entities,
    facts, records, or external data.
    """

    user_query: str
    searches: tuple[SearchRequest, ...]


@dataclass(frozen=True)
class EvidenceRecord:
    """
    A real record retrieved from the GraphOne datasets.

    The orchestration layer may reason over this evidence,
    but must not modify its factual contents.
    """

    dataset: DatasetName
    record_id: str
    payload: dict
    source_url: str
    raw_snapshot_sha256: str


@dataclass(frozen=True)
class GroundedResponse:
    """
    Final response generated from retrieved evidence.

    Every factual conclusion should be traceable to one
    or more EvidenceRecord objects.
    """

    answer: str
    evidence: tuple[EvidenceRecord, ...]