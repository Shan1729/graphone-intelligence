from __future__ import annotations

import asyncio
from pathlib import Path

from graphone.orchestration.gemini_planner import (
    GeminiPlanner,
)
from graphone.orchestration.grounded_responder import (
    GroundedResponder,
)
from graphone.orchestration.plan_validator import (
    PlanValidator,
)
from graphone.orchestration.router import (
    DatasetRouter,
)
from graphone.pipeline.orchestrator import (
    GraphOnePipeline,
)
from graphone.retrieval.evidence_ranker import (
    EvidenceRanker,
)
from graphone.retrieval.job_searcher import (
    JobSearcher,
)
from graphone.retrieval.news_searcher import (
    NewsSearcher,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


JOBS_FILE = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "jobs.jsonl"
)


NEWS_FILE = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "news.jsonl"
)


async def main() -> None:
    """
    End-to-end GraphOne pipeline test.

    Flow:

    User Query
        ↓
    GeminiPlanner
        ↓
    OrchestrationPlan
        ↓
    PlanValidator
        ↓
    Validated OrchestrationPlan
        ↓
    DatasetRouter
        ↓
    Raw Evidence Records
        ↓
    EvidenceRanker
        ↓
    Ranked Evidence Records
        ↓
    GroundedResponder
        ↓
    GroundedResponse
    """

    print(
        "=" * 80
    )

    print(
        "GRAPHONE END-TO-END PIPELINE TEST"
    )

    print(
        "=" * 80
    )

    print()

    if not JOBS_FILE.exists():

        raise FileNotFoundError(
            "Jobs dataset not found: "
            f"{JOBS_FILE}"
        )

    if not NEWS_FILE.exists():

        raise FileNotFoundError(
            "News dataset not found: "
            f"{NEWS_FILE}"
        )

    planner = (
        GeminiPlanner()
    )

    validator = (
        PlanValidator()
    )

    job_searcher = (
        JobSearcher(
            file_path=JOBS_FILE
        )
    )

    news_searcher = (
        NewsSearcher(
            file_path=NEWS_FILE
        )
    )

    router = (
        DatasetRouter(
            searchers={
                "jobs": job_searcher,
                "news": news_searcher,
            }
        )
    )

    ranker = (
        EvidenceRanker()
    )

    responder = (
        GroundedResponder()
    )

    pipeline = (
        GraphOnePipeline(
            planner=planner,
            validator=validator,
            router=router,
            ranker=ranker,
            responder=responder,
            evidence_limit=20,
        )
    )

    user_query = (
        "Find cybersecurity jobs and "
        "scientific literacy news"
    )

    print(
        "USER QUERY"
    )

    print(
        "-" * 80
    )

    print(
        user_query
    )

    print()

    print(
        "RUNNING GRAPHONE PIPELINE..."
    )

    print(
        "-" * 80
    )

    grounded_response = (
        await pipeline.run(
            user_query=user_query
        )
    )

    print()

    print(
        "=" * 80
    )

    print(
        "GROUNDED RESPONSE"
    )

    print(
        "=" * 80
    )

    print()

    print(
        grounded_response.answer
    )

    print()

    print(
        "=" * 80
    )

    print(
        "RANKED GROUNDING EVIDENCE"
    )

    print(
        "=" * 80
    )

    print()

    print(
        "TOTAL RANKED EVIDENCE RECORDS: "
        f"{len(grounded_response.evidence)}"
    )

    print()

    if not grounded_response.evidence:

        print(
            "No matching evidence records "
            "were retrieved."
        )

    else:

        for (
            index,
            record,
        ) in enumerate(
            grounded_response.evidence,
            start=1,
        ):

            payload = (
                record.payload
            )

            print(
                f"RESULT {index}"
            )

            print(
                f"Record ID: "
                f"{record.record_id}"
            )

            print(
                f"Dataset: "
                f"{record.dataset}"
            )

            print(
                f"Title: "
                f"{payload.get('title', '')}"
            )

            print(
                f"Name: "
                f"{payload.get('name', '')}"
            )

            print(
                f"Source: "
                f"{payload.get('source', '')}"
            )

            print(
                f"Published: "
                f"{payload.get('published_at', '')}"
            )

            print(
                f"Original URL: "
                f"{payload.get('url', '')}"
            )

            print(
                f"Source URL: "
                f"{record.source_url}"
            )

            print(
                f"Snapshot SHA-256: "
                f"{record.raw_snapshot_sha256}"
            )

            print()

    print(
        "=" * 80
    )

    print(
        "GRAPHONE PIPELINE TEST COMPLETE"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )