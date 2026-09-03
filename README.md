# graphone-intelligence
Production-grade AI intelligence ingestion pipeline for startups, products, research papers, jobs, and news.
# Graphone Intelligence

An asynchronous intelligence acquisition pipeline for collecting and processing signals related to startups, products, research papers, jobs, and news.

## Overview

Graphone Intelligence is a Python-based data acquisition system designed to collect intelligence signals from multiple online sources.

The project focuses on:

- Asynchronous web acquisition
- URL fetching with redirect support
- Configurable request timeouts
- SQLite-based storage
- SHA256-based acquisition deduplication
- Benchmarking
- Automated evaluation
- Failure and stress testing

## Project Features

### Async Data Fetching

The acquisition layer uses `httpx.AsyncClient` for asynchronous HTTP requests.

Features include:

- Asynchronous requests
- Redirect following
- Configurable timeouts
- Response content capture
- Final URL capture
- HTTP status code capture

### Data Deduplication

Acquisition records are protected against duplicate storage using SHA256-based identification.

This helps ensure that identical acquisition data is not unnecessarily stored multiple times.

### Storage

The project uses SQLite for lightweight local persistence.

The storage layer supports:

- Database initialization
- Acquisition storage
- SHA256 lookup
- Duplicate detection

### Failure Testing

The fetcher is tested against multiple response conditions:

- HTTP 200 — Successful response
- HTTP 429 — Rate limiting
- HTTP 500 — Server error
- Request timeout

### Benchmarking and Evaluation

The project includes:

- Benchmark harness
- Benchmark result collection
- Automated evaluation metric
- Full acquisition testing

## Project Structure

```text
graphone-intelligence/
│
├── src/
│   └── graphone/
│       ├── acquisition/
│       │   └── fetcher.py
│       │
│       ├── storage/
│       │   └── db.py
│       │
│       ├── benchmark.py
│       └── evaluation.py
│
├── tests/
│   ├── test_db.py
│   ├── test_fetcher.py
│   └── ...
│
├── README.md
└── requirements.txt