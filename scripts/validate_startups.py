import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


INPUT_FILE = Path("data/exports/startups.jsonl")

REQUIRED_FIELDS = {
    "schema_version",
    "record_type",
    "source_name",
    "source_url",
    "entity_name",
    "employee_count",
    "company_url",
    "website",
    "description",
    "industry",
    "location",
    "raw_snapshot_sha256",
    "collected_at",
}


def is_valid_http_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False

    try:
        parsed = urlparse(value)

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )

    except ValueError:
        return False


def is_valid_sha256(value: object) -> bool:
    if not isinstance(value, str):
        return False

    if len(value) != 64:
        return False

    try:
        int(value, 16)
        return True

    except ValueError:
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

    startup_names = []

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

        if record["record_type"] != "STARTUP":
            errors.append(
                f"Record {index}: Invalid record_type"
            )

        if record["source_name"] != "Y Combinator":
            errors.append(
                f"Record {index}: Unexpected source_name"
            )

        if not is_valid_http_url(
            record["source_url"]
        ):
            errors.append(
                f"Record {index}: Invalid source_url"
            )

        entity_name = record["entity_name"]

        if (
            not isinstance(entity_name, str)
            or not entity_name.strip()
        ):
            errors.append(
                f"Record {index}: Empty entity_name"
            )
        else:
            startup_names.append(
                entity_name.casefold().strip()
            )

        employee_count = record["employee_count"]

        if employee_count is not None:
            if (
                not isinstance(employee_count, int)
                or employee_count < 0
            ):
                errors.append(
                    f"Record {index}: Invalid employee_count"
                )

        for field in ("company_url", "website"):
            value = record[field]

            if value is not None and not is_valid_http_url(value):
                errors.append(
                    f"Record {index}: Invalid {field}"
                )

        for field in (
            "description",
            "industry",
            "location",
        ):
            value = record[field]

            if value is not None and not isinstance(value, str):
                errors.append(
                    f"Record {index}: Invalid {field}"
                )

        if not is_valid_sha256(
            record["raw_snapshot_sha256"]
        ):
            errors.append(
                f"Record {index}: Invalid raw_snapshot_sha256"
            )

        try:
            datetime.fromisoformat(
                record["collected_at"]
            )

        except (
            TypeError,
            ValueError,
        ):
            errors.append(
                f"Record {index}: Invalid collected_at"
            )

    name_counts = Counter(startup_names)

    duplicate_names = [
        name
        for name, count in name_counts.items()
        if count > 1
    ]

    if duplicate_names:
        errors.append(
            "Duplicate canonical startup names found: "
            f"{len(duplicate_names)}"
        )

    print("=" * 80)
    print("GRAPHONE STARTUP DATASET VALIDATION")
    print("=" * 80)

    print(f"Dataset: {INPUT_FILE}")
    print(f"Total records: {len(records)}")
    print(
        "Unique startup names: "
        f"{len(set(startup_names))}"
    )
    print(
        "Duplicate startup names: "
        f"{len(duplicate_names)}"
    )
    print(
        "Validation errors: "
        f"{len(errors)}"
    )

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
    print(
        "All startup records meet the current "
        "structural and provenance checks."
    )


if __name__ == "__main__":
    main()