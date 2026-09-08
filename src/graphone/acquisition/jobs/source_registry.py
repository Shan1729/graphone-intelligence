from __future__ import annotations


# Remotive is a general remote-job API.
REMOTIVE_API_URL = (
    "https://remotive.com/api/remote-jobs"
)


# Greenhouse public job-board API.
# Each value is a company job-board token.
GREENHOUSE_BOARDS = [
    "openai",
    "anthropic",
    "stripe",
]


# Lever public postings API.
# Add company site slugs here as needed.
LEVER_SITES = [
]


def greenhouse_url(
    board_token: str,
) -> str:
    return (
        "https://boards-api.greenhouse.io"
        f"/v1/boards/{board_token}/jobs"
    )


def lever_url(
    site: str,
) -> str:
    return (
        "https://api.lever.co"
        f"/v0/postings/{site}"
        "?mode=json"
    )