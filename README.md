# GraphOne Intelligence

An asynchronous, evidence-grounded intelligence acquisition and retrieval pipeline for collecting and processing signals related to startups, products, research papers, jobs, and news.

## Overview

GraphOne Intelligence is a Python-based intelligence retrieval system designed to collect, structure, search, rank, and synthesize evidence across multiple datasets.

The project focuses on:

- Asynchronous web acquisition
- URL fetching with redirect support
- Configurable request timeouts
- SQLite-based storage
- SHA-256-based acquisition deduplication
- Structured multi-dataset extraction
- Deterministic evidence retrieval
- LLM-based query planning
- Plan validation
- Dataset routing
- Evidence ranking
- Grounded response generation
- Benchmarking
- Automated evaluation
- Failure and stress testing

---

# Architecture

GraphOne separates language-model reasoning from evidence retrieval.

```text
User Query
    ↓
GeminiPlanner
    ↓
PlanValidator
    ↓
DatasetRouter
    ↓
Dataset Searchers
    ↓
Retrieved Evidence
    ↓
EvidenceRanker
    ↓
Ranked Evidence
    ↓
GroundedResponder
    ↓
Grounded Response
```

The LLM is responsible for understanding and planning the query.

Dataset searchers are responsible for retrieving structured evidence from the stored datasets.

This architecture helps ensure that evidence retrieval remains deterministic and traceable.

---

# Supported Intelligence Domains

GraphOne currently supports five intelligence domains:

1. Startups
2. Products
3. Research Papers
4. Jobs
5. News

Each domain has:

- Its own JSONL dataset
- Its own dedicated searcher
- Dataset-specific searchable fields
- Dataset-specific field weighting
- Dataset-specific aliases
- Dataset-specific stopwords
- Dataset-specific validation

---

# Datasets

## 1. Startups

The startup dataset contains structured startup intelligence.

Retrieved information can include:

- Startup name
- Description
- Website
- Industry
- Location
- Source URL
- Snapshot SHA-256
- Collection timestamp

Dataset:

```text
data/exports/startups.jsonl
```

Retrieval is performed using:

```text
StartupSearcher
```

---

## 2. Products

The product dataset contains structured product intelligence records.

Product records are normalized into a unified schema.

Dataset:

```text
data/exports/products.jsonl
```

Retrieval is performed using:

```text
ProductSearcher
```

Searchable fields include:

- `product_name`
- `brand`
- `description`
- `category`
- `quantity`

### Field Weighting

| Field | Weight |
|---|---:|
| Product Name | 5 |
| Brand | 4 |
| Category | 3 |
| Description | 2 |
| Quantity | 1 |

The product searcher also supports dataset-specific aliases and stopwords.

No LLM is used to generate product records during retrieval.

### Product Record Validation

A product record must contain:

- `product_name`
- `barcode`
- `product_url`

A record is considered valid only when these fields contain non-empty string values.

This ensures that product evidence satisfies the minimum structural requirements expected by the retrieval system.

### Example Product Record

```json
{
    "schema_version": "1.0",
    "record_type": "PRODUCT",
    "source_name": "Open Food Facts",
    "source_url": "SOURCE_URL",
    "product_name": "Example Product",
    "product_url": "PRODUCT_URL",
    "barcode": "123456789",
    "brand": "Example Brand",
    "description": "Example product description",
    "category": "Example category",
    "quantity": "500 g",
    "raw_snapshot_sha256": "SHA256_HASH",
    "collected_at": "TIMESTAMP"
}
```

The exact contents depend on the acquired source evidence.

---

## 3. Research Papers

The research paper dataset contains structured information about research publications.

Retrieved information can include:

- Paper title
- Authors
- Publication date
- Paper URL
- GitHub URL where available
- GitHub stars where available
- Source URL
- Snapshot SHA-256

Dataset:

```text
data/exports/research_papers.jsonl
```

Retrieval is performed using:

```text
ResearchPaperSearcher
```

---

## 4. Jobs

The jobs dataset contains structured job intelligence.

Typical information includes:

- Job title
- Company
- Location
- Source
- Publication date
- Original job URL
- Source URL
- Snapshot SHA-256

Dataset:

```text
data/exports/jobs.jsonl
```

Retrieval is performed using:

```text
JobSearcher
```

---

## 5. News

The news dataset contains acquired news intelligence records.

Typical information includes:

- News title
- Source
- Publication date
- Original URL
- Source URL
- Snapshot SHA-256

Dataset:

```text
data/exports/news.jsonl
```

Retrieval is performed using:

```text
NewsSearcher
```

---

# Key Features

## Multi-Dataset Query Processing

A single user query can span multiple intelligence domains.

For example, one request can simultaneously ask for:

- Startups
- Products
- Research papers
- Jobs
- News

The orchestration layer determines how the query should be routed.

---

## LLM-Based Query Planning

The system uses:

```text
GeminiPlanner
```

to convert a natural-language request into a structured orchestration plan.

The planner is responsible for understanding:

- What the user is requesting
- Which datasets are relevant
- How the request should be decomposed

The planner does not directly retrieve evidence.

---

## Plan Validation

The orchestration plan is passed through:

```text
PlanValidator
```

before retrieval.

This creates a validation boundary between LLM-generated planning and downstream retrieval.

The validated plan is then passed to the dataset routing layer.

---

## Dataset Routing

The:

```text
DatasetRouter
```

maps validated retrieval tasks to the appropriate dataset searchers.

The router currently supports:

- `startups`
- `products`
- `research_papers`
- `jobs`
- `news`

Each dataset has its own dedicated searcher.

---

# Deterministic Retrieval

GraphOne deliberately separates language-model reasoning from evidence retrieval.

The LLM is responsible for:

```text
Query Understanding
        +
Query Planning
```

Dataset searchers are responsible for:

```text
Deterministic Evidence Retrieval
```

This means that retrieval is based on stored records rather than unrestricted model generation.

Benefits include:

- Reproducible retrieval behavior
- Evidence traceability
- Controlled dataset access
- Dataset-specific validation
- Reduced hallucination during retrieval

---

# Evidence Ranking

Retrieved records are passed to:

```text
EvidenceRanker
```

The ranking layer processes the retrieved evidence and selects the most relevant records for the user query.

The flow is:

```text
Raw Retrieved Evidence
        ↓
EvidenceRanker
        ↓
Ranked Evidence
        ↓
Top Relevant Records
```

The number of evidence records passed into the response stage can be controlled through the pipeline configuration.

Example:

```python
GraphOnePipeline(
    planner=planner,
    validator=validator,
    router=router,
    ranker=ranker,
    responder=responder,
    evidence_limit=20,
)
```

---

# Grounded Responses

The:

```text
GroundedResponder
```

generates the final user-facing response using the ranked evidence records.

The response generation stage receives evidence rather than independently retrieving data.

The resulting response contains:

```text
Grounded Answer
        +
Ranked Evidence Records
```

This allows the pipeline to preserve the connection between generated information and the underlying retrieved evidence.

---

# Data Provenance

GraphOne preserves provenance information for acquired records.

Depending on the dataset, records can contain:

- `source_url`
- `raw_snapshot_sha256`
- `collected_at`

The SHA-256 value provides a cryptographic identifier for the acquired raw data snapshot.

This supports:

- Evidence provenance
- Source traceability
- Dataset reproducibility
- Verification of acquired snapshots

---

# Product Bulk Extraction

The project includes a one-time bulk product extraction pipeline.

The extractor supports processing local bulk source files and exporting normalized product records into:

```text
data/exports/products.jsonl
```

The bulk extractor includes:

- Streaming input processing
- Gzip support
- JSONL processing
- Record normalization
- SHA-256 snapshot generation
- Source provenance
- Record deduplication
- Incremental appending

The extractor maintains a deduplication key based on:

```text
source_name + barcode
```

This allows future extraction runs to avoid writing duplicate records already present in the export.

---

# Project Structure

```text
graphone-intelligence/
│
├── data/
│   │
│   ├── exports/
│   │   ├── startups.jsonl
│   │   ├── products.jsonl
│   │   ├── research_papers.jsonl
│   │   ├── jobs.jsonl
│   │   └── news.jsonl
│   │
│   └── raw/
│       └── products/
│
├── scripts/
│   │
│   ├── bulk_products.py
│   ├── extract_products.py
│   ├── extract_startups.py
│   ├── extract_research_papers.py
│   ├── extract_jobs.py
│   ├── extract_news.py
│   │
│   ├── preview_products.py
│   ├── preview_startups.py
│   ├── preview_research_papers.py
│   │
│   ├── test_product_retrieval.py
│   ├── test_startup_retrieval.py
│   ├── test_research_paper_retrieval.py
│   ├── test_job_retrieval.py
│   ├── test_news_retrieval.py
│   │
│   ├── test_router.py
│   ├── test_pipeline.py
│   ├── test_multi_dataset_pipeline.py
│   ├── test_full_pipeline.py
│   └── test_full_graphone_pipeline.py
│
├── src/
│   │
│   └── graphone/
│       │
│       ├── acquisition/
│       │   └── fetcher.py
│       │
│       ├── orchestration/
│       │   ├── gemini_planner.py
│       │   ├── grounded_responder.py
│       │   ├── plan_validator.py
│       │   └── router.py
│       │
│       ├── pipeline/
│       │   └── orchestrator.py
│       │
│       ├── retrieval/
│       │   ├── base_searcher.py
│       │   ├── evidence_ranker.py
│       │   ├── startup_searcher.py
│       │   ├── product_searcher.py
│       │   ├── research_paper_searcher.py
│       │   ├── job_searcher.py
│       │   └── news_searcher.py
│       │
│       └── storage/
│           └── db.py
│
├── README.md
└── requirements.txt
```

---

# Installation

Clone the repository:

```bash
git clone https://github.com/Shan1729/graphone-intelligence.git
```

Move into the project directory:

```bash
cd graphone-intelligence
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate the environment on Windows:

```bash
.venv\Scripts\activate
```

Install project dependencies:

```bash
pip install -r requirements.txt
```

---

# Configuration

The orchestration pipeline uses Gemini-based planner and responder components.

Ensure that the required environment configuration for the Gemini integration is available before running the full pipeline.

The exact environment variables depend on the Gemini client configuration used by the project.

---

# Running the Full Pipeline

From the project root, run:

```bash
python scripts/test_full_pipeline.py
```

The full pipeline performs the following steps:

1. Check dataset availability
2. Initialize `GeminiPlanner`
3. Initialize `PlanValidator`
4. Initialize dataset searchers
5. Initialize `DatasetRouter`
6. Initialize `EvidenceRanker`
7. Initialize `GroundedResponder`
8. Initialize `GraphOnePipeline`
9. Execute the user query
10. Generate a grounded response
11. Display ranked grounding evidence

---

# Example Query

The full pipeline can process a multi-dataset query such as:

```text
Find AI startups, AI products,
research papers about artificial intelligence,
cybersecurity jobs, and recent artificial
intelligence news.
```

The query is processed across multiple datasets.

---

# Example Output

The final system produces a grounded response organized by the requested intelligence categories.

For example:

```text
AI Startups
    • Retrieved startup intelligence

AI Products
    • Retrieved product evidence

Research Papers
    • Retrieved research paper evidence

Cybersecurity Jobs
    • Retrieved job evidence

Recent AI News
    • Retrieved news evidence
```

The pipeline additionally displays ranked evidence records used for grounding.

---

# Testing

The project contains dataset-specific and pipeline-level test scripts.

## Product Retrieval

```bash
python scripts/test_product_retrieval.py
```

## Startup Retrieval

```bash
python scripts/test_startup_retrieval.py
```

## Research Paper Retrieval

```bash
python scripts/test_research_paper_retrieval.py
```

## Job Retrieval

```bash
python scripts/test_job_retrieval.py
```

## News Retrieval

```bash
python scripts/test_news_retrieval.py
```

## Dataset Router

```bash
python scripts/test_router.py
```

## Multi-Dataset Pipeline

```bash
python scripts/test_multi_dataset_pipeline.py
```

## Full Pipeline

```bash
python scripts/test_full_pipeline.py
```

---

# Technology Stack

GraphOne Intelligence uses:

- Python
- AsyncIO
- HTTPX
- JSONL
- SQLite
- SHA-256
- Google Gemini
- Structured data extraction
- Deterministic retrieval
- Evidence ranking
- Grounded response generation

---

# Design Principles

## Evidence First

Responses are intended to be grounded in retrieved dataset evidence.

## Separation of Concerns

Planning, validation, retrieval, ranking, and response generation are implemented as separate stages.

## Deterministic Retrieval

The retrieval layer does not rely on an LLM to invent or generate dataset records.

Dataset searchers operate on stored evidence.

## Dataset Isolation

Each intelligence domain has its own dataset searcher.

This allows dataset-specific:

- Searchable fields
- Field weights
- Aliases
- Stopwords
- Record validation

## Provenance

Records preserve information about their origin and acquired raw data snapshots.

## Controlled Orchestration

LLM-generated orchestration plans are validated before they reach the retrieval layer.

---

# Current Scope

GraphOne Intelligence currently focuses on structured intelligence retrieval across five domains:

- Startups
- Products
- Research Papers
- Jobs
- News

The project demonstrates a complete pipeline from natural-language query interpretation to evidence-grounded response generation.

---

# Future Improvements

Potential future improvements include:

- Larger datasets
- Additional intelligence domains
- Incremental dataset updates
- Automated freshness monitoring
- Hybrid lexical and semantic retrieval
- Advanced evidence ranking
- Query evaluation benchmarks
- Web interface
- REST API
- Deployment infrastructure
- Dataset update scheduling

---

# Conclusion

GraphOne Intelligence demonstrates an architecture for building evidence-grounded intelligence systems where language models are used for controlled planning and response synthesis while dataset retrieval remains deterministic.

By separating planning, validation, routing, retrieval, ranking, and response generation, the system provides a structured foundation for multi-dataset intelligence retrieval with evidence traceability and provenance.