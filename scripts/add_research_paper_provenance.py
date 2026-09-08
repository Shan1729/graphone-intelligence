from __future__ import annotations

import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]


INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "research_papers.jsonl"
)


TEMP_FILE = (
    PROJECT_ROOT
    / "data"
    / "exports"
    / "research_papers.with_provenance.jsonl"
)


def sha256_file(
    file_path: Path,
) -> str:
    """
    Calculate a deterministic SHA-256 fingerprint
    for the existing acquired research-paper dataset.
    """

    digest = hashlib.sha256()

    with file_path.open(
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def main() -> None:

    print("=" * 80)
    print(
        "GRAPHONE RESEARCH PAPER "
        "PROVENANCE MIGRATION"
    )
    print("=" * 80)

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            "Research paper dataset not found: "
            f"{INPUT_FILE}"
        )

    snapshot_sha256 = (
        sha256_file(
            INPUT_FILE
        )
    )

    print()
    print(
        "Input file:"
    )
    print(
        INPUT_FILE
    )

    print()
    print(
        "Dataset SHA-256:"
    )
    print(
        snapshot_sha256
    )

    records_written = 0
    records_skipped = 0

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as input_file, TEMP_FILE.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for line_number, line in enumerate(
            input_file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:

                record = json.loads(
                    line
                )

            except json.JSONDecodeError:

                records_skipped += 1

                print(
                    "Skipping invalid JSON "
                    f"at line {line_number}"
                )

                continue

            if not isinstance(
                record,
                dict,
            ):

                records_skipped += 1

                continue

            if (
                record.get(
                    "record_type"
                )
                != "RESEARCH_PAPER"
            ):

                records_skipped += 1

                continue

            record[
                "raw_snapshot_sha256"
            ] = snapshot_sha256

            output_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

            records_written += 1

    INPUT_FILE.replace(
        PROJECT_ROOT
        / "data"
        / "exports"
        / "research_papers.backup.jsonl"
    )

    TEMP_FILE.replace(
        INPUT_FILE
    )

    print()
    print("=" * 80)
    print(
        "PROVENANCE MIGRATION COMPLETE"
    )
    print("=" * 80)

    print(
        f"Records updated: "
        f"{records_written}"
    )

    print(
        f"Records skipped: "
        f"{records_skipped}"
    )

    print(
        "Backup created:"
    )

    print(
        PROJECT_ROOT
        / "data"
        / "exports"
        / "research_papers.backup.jsonl"
    )

    print(
        "Updated dataset:"
    )

    print(
        INPUT_FILE
    )

    print()
    print(
        "Every retained research paper now "
        "contains raw_snapshot_sha256."
    )


if __name__ == "__main__":

    main()