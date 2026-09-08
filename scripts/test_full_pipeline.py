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


def print_record_details(
    record,
) -> None:
    """
    Print dataset-specific evidence fields.

    Evidence payloads are preserved exactly as acquired.
    This function only chooses the appropriate fields
    to display for each dataset.
    """

    payload = record.payload

    print(
        f"Record ID: "
        f"{record.record_id}"
    )

    print(
        f"Dataset: "
        f"{record.dataset}"
    )

    if record.dataset == "startups":

        print(
            f"Name: "
            f"{payload.get('entity_name', '')}"
        )

        print(
            f"Industry: "
            f"{payload.get('industry', '')}"
        )

        print(
            f"Location: "
            f"{payload.get('location', '')}"
        )

        print(
            f"Employees: "
            f"{payload.get('employee_count', '')}"
        )

        print(
            f"Source: "
            f"{payload.get('source_name', '')}"
        )

        print(
            f"Company URL: "
            f"{payload.get('company_url', '')}"
        )

        print(
            f"Website: "
            f"{payload.get('website', '')}"
        )

    elif record.dataset == "products":

        print(
            f"Product Name: "
            f"{payload.get('product_name', '')}"
        )

        print(
            f"Brand: "
            f"{payload.get('brand', '')}"
        )

        print(
            f"Category: "
            f"{payload.get('category', '')}"
        )

        print(
            f"Quantity: "
            f"{payload.get('quantity', '')}"
        )

        print(
            f"Barcode: "
            f"{payload.get('barcode', '')}"
        )

        print(
            f"Source: "
            f"{payload.get('source_name', '')}"
        )

        print(
            f"Product URL: "
            f"{payload.get('product_url', '')}"
        )

    elif (
        record.dataset
        == "research_papers"
    ):

        print(
            f"Title: "
            f"{payload.get('title', '')}"
        )

        print(
            f"Authors: "
            f"{', '.join(payload.get('authors', []))}"
        )

        print(
            f"Published: "
            f"{payload.get('published_date', '')}"
        )

        print(
            f"Paper URL: "
            f"{payload.get('paper_url', '')}"
        )

        print(
            f"GitHub URL: "
            f"{payload.get('github_url', '')}"
        )

        print(
            f"GitHub Stars: "
            f"{payload.get('github_stars', '')}"
        )

    elif record.dataset == "jobs":

        print(
            f"Title: "
            f"{payload.get('title', '')}"
        )

        print(
            f"Company: "
            f"{payload.get('company', '')}"
        )

        print(
            f"Location: "
            f"{payload.get('location', '')}"
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

    elif record.dataset == "news":

        print(
            f"Title: "
            f"{payload.get('title', '')}"
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


async def main() -> None:
    """
    Full end-to-end GraphOne pipeline test.

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
    Top Relevant Evidence Records
        ↓
    GroundedResponder
        ↓
    GroundedResponse
    """

    print(
        "=" * 80
    )

    print(
        "GRAPHONE FULL PIPELINE TEST"
    )

    print(
        "=" * 80
    )

    print()

    dataset_files = {
        "Startups": STARTUPS_FILE,
        "Products": PRODUCTS_FILE,
        "Research Papers": (
            RESEARCH_PAPERS_FILE
        ),
        "Jobs": JOBS_FILE,
        "News": NEWS_FILE,
    }

    print(
        "CHECKING DATASETS"
    )

    print(
        "-" * 80
    )

    for (
        dataset_name,
        file_path,
    ) in dataset_files.items():

        if not file_path.exists():

            raise FileNotFoundError(
                f"{dataset_name} dataset not found: "
                f"{file_path}"
            )

        print(
            f"[OK] {dataset_name}: "
            f"{file_path}"
        )

    print()

    print(
        "INITIALIZING GRAPHONE COMPONENTS..."
    )

    print(
        "-" * 80
    )

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
            file_path=(
                RESEARCH_PAPERS_FILE
            )
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
                "startups": (
                    startup_searcher
                ),
                "products": (
                    product_searcher
                ),
                "research_papers": (
                    research_paper_searcher
                ),
                "jobs": (
                    job_searcher
                ),
                "news": (
                    news_searcher
                ),
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

    print(
        "[OK] GeminiPlanner initialized"
    )

    print(
        "[OK] PlanValidator initialized"
    )

    print(
        "[OK] All five dataset searchers initialized"
    )

    print(
        "[OK] DatasetRouter initialized"
    )

    print(
        "[OK] EvidenceRanker initialized"
    )

    print(
        "[OK] GroundedResponder initialized"
    )

    print(
        "[OK] GraphOnePipeline initialized"
    )

    print()

    user_query = (
        "Find AI startups, AI products, "
        "research papers about artificial intelligence, "
        "cybersecurity jobs, and recent artificial "
        "intelligence news"
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
        "RUNNING GRAPHONE FULL PIPELINE..."
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

            print(
                f"RESULT {index}"
            )

            print_record_details(
                record
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