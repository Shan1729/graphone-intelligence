import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


INPUT_FILE = Path("data/exports/research_papers.jsonl")

REQUIRED_FIELDS = {
    "schema_version",
    "record_type",
    "title",
    "authors",
    "paper_url",
    "github_url",
    "github_stars",
    "published_date",
    "source_url",
}


def is_valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    records = []
    errors = []

    with INPUT_FILE.open(
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
                record = json.loads(line)
                records.append(record)

            except json.JSONDecodeError as exc:
                errors.append(
                    f"Line {line_number}: Invalid JSON - {exc}"
                )

    paper_urls = []
    dates = []

    for index, record in enumerate(
        records,
        start=1,
    ):
        missing_fields = (
            REQUIRED_FIELDS - record.keys()
        )

        if missing_fields:
            errors.append(
                f"Record {index}: Missing fields "
                f"{sorted(missing_fields)}"
            )
            continue

        if record["schema_version"] != "1.0":
            errors.append(
                f"Record {index}: Invalid schema_version"
            )

        if record["record_type"] != "RESEARCH_PAPER":
            errors.append(
                f"Record {index}: Invalid record_type"
            )

        if not isinstance(record["title"], str) or not record["title"].strip():
            errors.append(
                f"Record {index}: Empty or invalid title"
            )

        if (
            not isinstance(record["authors"], list)
            or not record["authors"]
        ):
            errors.append(
                f"Record {index}: Missing authors"
            )

        if not is_valid_http_url(record["paper_url"]):
            errors.append(
                f"Record {index}: Invalid paper_url"
            )
        else:
            paper_urls.append(
                record["paper_url"]
            )

        if not is_valid_http_url(record["source_url"]):
            errors.append(
                f"Record {index}: Invalid source_url"
            )

        if record["source_url"] != record["paper_url"]:
            errors.append(
                f"Record {index}: source_url does not match paper_url"
            )

        try:
            parsed_date = datetime.fromisoformat(
                record["published_date"]
            )
            dates.append(parsed_date)

        except (TypeError, ValueError):
            errors.append(
                f"Record {index}: Invalid published_date"
            )

        github_url = record["github_url"]
        github_stars = record["github_stars"]

        if github_url is not None:
            if not is_valid_http_url(github_url):
                errors.append(
                    f"Record {index}: Invalid github_url"
                )

        if github_stars is not None:
            if (
                not isinstance(github_stars, int)
                or github_stars < 0
            ):
                errors.append(
                    f"Record {index}: Invalid github_stars"
                )

    url_counts = Counter(paper_urls)

    duplicate_urls = [
        url
        for url, count in url_counts.items()
        if count > 1
    ]

    if duplicate_urls:
        errors.append(
            f"Duplicate paper URLs found: "
            f"{len(duplicate_urls)}"
        )

    print("=" * 80)
    print("GRAPHONE RESEARCH PAPER DATASET VALIDATION")
    print("=" * 80)

    print(f"Dataset: {INPUT_FILE}")
    print(f"Total records: {len(records)}")
    print(f"Unique paper URLs: {len(set(paper_urls))}")
    print(f"Duplicate paper URLs: {len(duplicate_urls)}")

    if dates:
        print(
            "Oldest publication: "
            f"{min(dates).isoformat()}"
        )
        print(
            "Newest publication: "
            f"{max(dates).isoformat()}"
        )

    print(f"Validation errors: {len(errors)}")

    if errors:
        print()
        print("VALIDATION FAILED")
        print("-" * 80)

        for error in errors[:20]:
            print(error)

        if len(errors) > 20:
            print(
                f"... and {len(errors) - 20} more errors"
            )

        raise SystemExit(1)

    print()
    print("VALIDATION PASSED")
    print("All records meet the current structural checks.")


if __name__ == "__main__":
    main()