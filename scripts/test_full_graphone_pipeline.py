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
from graphone.retrieval.job_searcher import (
    JobSearcher,
)
from graphone.retrieval.news_searcher import (
    NewsSearcher,
)
from graphone.retrieval.product_searcher import (
    ProductSearcher,
)
from graphone.retrieval.research_paper_searcher import (
    ResearchPaperSearcher,
)
from graphone.retrieval.startup_searcher import (
    StartupSearcher,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


STARTUPS_FILE = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "startups.jsonl"
)


PRODUCTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "products.jsonl"
)


RESEARCH_PAPERS_FILE = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "research_papers.jsonl"
)


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

    print(
        "=" * 80
    )

    print(
        "GRAPHONE FULL FIVE-DATASET PIPELINE TEST"
    )

    print(
        "=" * 80
    )

    print()

    dataset_files = {
        "startups": STARTUPS_FILE,
        "products": PRODUCTS_FILE,
        "research_papers": RESEARCH_PAPERS_FILE,
        "jobs": JOBS_FILE,
        "news": NEWS_FILE,
    }

    print(
        "CHECKING DATASETS..."
    )

    print(
        "-" * 80
    )

    for (
        dataset,
        file_path,
    ) in dataset_files.items():

        if not file_path.exists():

            raise FileNotFoundError(
                f"{dataset} dataset not found: "
                f"{file_path}"
            )

        print(
            f"FOUND: {dataset}"
        )

    print()

    planner = (
        GeminiPlanner()
    )

    validator = (
        PlanValidator()
    )

    startup_searcher = (
        StartupSearcher(
            file_path=STARTUPS_FILE
        )
    )

    product_searcher = (
        ProductSearcher(
            file_path=PRODUCTS_FILE
        )
    )

    research_paper_searcher = (
        ResearchPaperSearcher(
            file_path=RESEARCH_PAPERS_FILE
        )
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
                "startups": startup_searcher,
                "products": product_searcher,
                "research_papers": (
                    research_paper_searcher
                ),
                "jobs": job_searcher,
                "news": news_searcher,
            }
        )
    )

    responder = (
        GroundedResponder()
    )

    pipeline = (
        GraphOnePipeline(
            planner=planner,
            validator=validator,
            router=router,
            responder=responder,
        )
    )

    user_query = (
        "Find AI startups, AI products, "
        "research papers about artificial "
        "intelligence, AI jobs, and recent "
        "artificial intelligence news"
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
        "RUNNING FULL GRAPHONE PIPELINE..."
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
        "GROUNDING EVIDENCE"
    )

    print(
        "=" * 80
    )

    print()

    print(
        "TOTAL EVIDENCE RECORDS: "
        f"{len(grounded_response.evidence)}"
    )

    print()

    dataset_counts: dict[
        str,
        int,
    ] = {}

    for record in grounded_response.evidence:

        dataset_counts[
            record.dataset
        ] = (
            dataset_counts.get(
                record.dataset,
                0,
            )
            + 1
        )

    print(
        "EVIDENCE BY DATASET"
    )

    print(
        "-" * 80
    )

    for (
        dataset,
        count,
    ) in sorted(
        dataset_counts.items()
    ):

        print(
            f"{dataset}: {count}"
        )

    print()

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
            "=" * 80
        )

        print(
            f"RESULT {index}"
        )

        print(
            "=" * 80
        )

        print(
            f"Record ID: "
            f"{record.record_id}"
        )

        print(
            f"Dataset: "
            f"{record.dataset}"
        )

        print()

        print(
            "PAYLOAD"
        )

        print(
            "-" * 80
        )

        for (
            key,
            value,
        ) in payload.items():

            print(
                f"{key}: {value}"
            )

        print()

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
        "GRAPHONE FULL PIPELINE TEST COMPLETE"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )