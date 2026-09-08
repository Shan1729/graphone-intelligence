from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import quote


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "products"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "exports"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "products.jsonl"
)


OPEN_FOOD_FACTS_SOURCE_URL = (
    "https://static.openfoodfacts.org/"
    "data/openfoodfacts-products.jsonl.gz"
)


OPEN_LIBRARY_SOURCE_URL = (
    "https://openlibrary.org/"
    "developers/dumps"
)


@dataclass(frozen=True)
class Product:
    """
    Unified GraphOne product record.

    Every record is derived from an acquired source.
    No LLM-generated product fields are used.
    """

    schema_version: str
    record_type: str
    source_name: str
    source_url: str
    product_name: str
    product_url: str
    barcode: str
    brand: str | None
    description: str | None
    category: str | None
    quantity: str | None
    raw_snapshot_sha256: str
    collected_at: str


def normalize_text(
    value: object,
) -> str | None:

    if not isinstance(
        value,
        str,
    ):
        return None

    value = " ".join(
        value.split()
    )

    return value or None


def sha256_file(
    file_path: Path,
) -> str:

    digest = hashlib.sha256()

    with file_path.open(
        "rb",
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


def open_text_stream(
    file_path: Path,
):

    if (
        file_path.suffix
        == ".gz"
    ):

        return gzip.open(
            file_path,
            "rt",
            encoding="utf-8",
            errors="replace",
        )

    return file_path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    )


def load_existing_record_keys(
    file_path: Path,
) -> set[
    tuple[
        str,
        str,
    ]
]:
    """
    Load source_name + barcode keys already present
    in the GraphOne product export.

    This allows future extraction runs to append only
    genuinely new records.
    """

    seen_records: set[
        tuple[
            str,
            str,
        ]
    ] = set()

    if not file_path.exists():
        return seen_records

    with file_path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:

                record = json.loads(
                    line
                )

            except json.JSONDecodeError:

                continue

            if not isinstance(
                record,
                dict,
            ):
                continue

            source_name = normalize_text(
                record.get(
                    "source_name"
                )
            )

            barcode = normalize_text(
                record.get(
                    "barcode"
                )
            )

            if (
                source_name
                and barcode
            ):

                seen_records.add(
                    (
                        source_name,
                        barcode,
                    )
                )

    return seen_records


def count_existing_records(
    file_path: Path,
) -> int:

    if not file_path.exists():
        return 0

    count = 0

    with file_path.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:

        for line in file:

            if line.strip():
                count += 1

    return count


def build_off_product_url(
    barcode: str,
) -> str:

    return (
        "https://world.openfoodfacts.org/"
        "product/"
        f"{quote(barcode)}"
    )


def build_open_library_url(
    edition_key: str,
) -> str:

    return (
        "https://openlibrary.org"
        f"{edition_key}"
    )


def parse_open_food_facts(
    file_path: Path,
    snapshot_sha256: str,
    collected_at: str,
    limit: int,
) -> Iterator[Product]:

    yielded = 0

    with open_text_stream(
        file_path
    ) as file:

        for line in file:

            if yielded >= limit:
                return

            line = line.strip()

            if not line:
                continue

            try:

                raw = json.loads(
                    line
                )

            except json.JSONDecodeError:

                continue

            if not isinstance(
                raw,
                dict,
            ):
                continue

            barcode = normalize_text(
                raw.get(
                    "code"
                )
            )

            product_name = normalize_text(
                raw.get(
                    "product_name"
                )
            )

            if (
                not barcode
                or not product_name
            ):
                continue

            product_url = normalize_text(
                raw.get(
                    "url"
                )
            )

            if not product_url:

                product_url = (
                    build_off_product_url(
                        barcode
                    )
                )

            product = Product(
                schema_version="1.0",
                record_type="PRODUCT",
                source_name=(
                    "Open Food Facts"
                ),
                source_url=(
                    OPEN_FOOD_FACTS_SOURCE_URL
                ),
                product_name=product_name,
                product_url=product_url,
                barcode=barcode,
                brand=normalize_text(
                    raw.get(
                        "brands"
                    )
                ),
                description=normalize_text(
                    raw.get(
                        "generic_name"
                    )
                ),
                category=normalize_text(
                    raw.get(
                        "categories"
                    )
                ),
                quantity=normalize_text(
                    raw.get(
                        "quantity"
                    )
                ),
                raw_snapshot_sha256=(
                    snapshot_sha256
                ),
                collected_at=(
                    collected_at
                ),
            )

            yielded += 1

            yield product


def parse_open_library_line(
    line: str,
) -> dict | None:

    parts = line.rstrip(
        "\n"
    ).split(
        "\t",
        maxsplit=4,
    )

    if len(parts) != 5:
        return None

    (
        _record_type,
        key,
        _revision,
        _last_modified,
        json_payload,
    ) = parts

    try:

        payload = json.loads(
            json_payload
        )

    except json.JSONDecodeError:

        return None

    if not isinstance(
        payload,
        dict,
    ):
        return None

    payload[
        "_graphone_key"
    ] = key

    return payload


def extract_open_library_title(
    raw: dict,
) -> str | None:

    return normalize_text(
        raw.get(
            "title"
        )
    )


def extract_open_library_isbn(
    raw: dict,
) -> str | None:

    isbn_13 = raw.get(
        "isbn_13"
    )

    if isinstance(
        isbn_13,
        list,
    ):

        for value in isbn_13:

            normalized = (
                normalize_text(
                    value
                )
            )

            if normalized:
                return normalized

    isbn_10 = raw.get(
        "isbn_10"
    )

    if isinstance(
        isbn_10,
        list,
    ):

        for value in isbn_10:

            normalized = (
                normalize_text(
                    value
                )
            )

            if normalized:
                return normalized

    return normalize_text(
        raw.get(
            "_graphone_key"
        )
    )


def parse_open_library(
    file_path: Path,
    snapshot_sha256: str,
    collected_at: str,
    limit: int,
) -> Iterator[Product]:

    yielded = 0

    with open_text_stream(
        file_path
    ) as file:

        for line in file:

            if yielded >= limit:
                return

            raw = (
                parse_open_library_line(
                    line
                )
            )

            if raw is None:
                continue

            edition_key = normalize_text(
                raw.get(
                    "_graphone_key"
                )
            )

            product_name = (
                extract_open_library_title(
                    raw
                )
            )

            barcode = (
                extract_open_library_isbn(
                    raw
                )
            )

            if (
                not edition_key
                or not product_name
                or not barcode
            ):
                continue

            publishers = raw.get(
                "publishers"
            )

            brand = None

            if isinstance(
                publishers,
                list,
            ):

                publisher_values = []

                for publisher in publishers:

                    normalized = (
                        normalize_text(
                            publisher
                        )
                    )

                    if normalized:

                        publisher_values.append(
                            normalized
                        )

                if publisher_values:

                    brand = (
                        ", ".join(
                            publisher_values[
                                :3
                            ]
                        )
                    )

            subjects = raw.get(
                "subjects"
            )

            category = None

            if isinstance(
                subjects,
                list,
            ):

                subject_values = []

                for subject in subjects:

                    normalized = (
                        normalize_text(
                            subject
                        )
                    )

                    if normalized:

                        subject_values.append(
                            normalized
                        )

                if subject_values:

                    category = (
                        ", ".join(
                            subject_values[
                                :5
                            ]
                        )
                    )

            description = normalize_text(
                raw.get(
                    "subtitle"
                )
            )

            number_of_pages = raw.get(
                "number_of_pages"
            )

            quantity = None

            if isinstance(
                number_of_pages,
                int,
            ):

                quantity = (
                    f"{number_of_pages} pages"
                )

            product = Product(
                schema_version="1.0",
                record_type="PRODUCT",
                source_name=(
                    "Open Library"
                ),
                source_url=(
                    OPEN_LIBRARY_SOURCE_URL
                ),
                product_name=product_name,
                product_url=(
                    build_open_library_url(
                        edition_key
                    )
                ),
                barcode=barcode,
                brand=brand,
                description=description,
                category=category,
                quantity=quantity,
                raw_snapshot_sha256=(
                    snapshot_sha256
                ),
                collected_at=(
                    collected_at
                ),
            )

            yielded += 1

            yield product


def write_product(
    file,
    product: Product,
) -> None:

    file.write(
        json.dumps(
            asdict(
                product
            ),
            ensure_ascii=False,
        )
        + "\n"
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "GraphOne one-time "
            "multi-source product "
            "bulk extractor"
        )
    )

    parser.add_argument(
        "--off-file",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--openlibrary-file",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--off-limit",
        type=int,
        default=10000,
    )

    parser.add_argument(
        "--openlibrary-limit",
        type=int,
        default=10000,
    )

    args = parser.parse_args()

    if (
        args.off_limit < 0
        or args.openlibrary_limit < 0
    ):
        raise ValueError(
            "Extraction limits must "
            "be >= 0"
        )

    if (
        args.off_file is None
        and args.openlibrary_file is None
    ):
        raise ValueError(
            "Provide at least one "
            "bulk source file."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    collected_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    existing_record_count = (
        count_existing_records(
            OUTPUT_FILE
        )
    )

    seen_records = (
        load_existing_record_keys(
            OUTPUT_FILE
        )
    )

    total_written = 0

    source_counts = {
        "Open Food Facts": 0,
        "Open Library": 0,
    }

    print("=" * 80)
    print(
        "GRAPHONE MULTI-SOURCE "
        "PRODUCT BULK EXTRACTION"
    )
    print("=" * 80)

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        f"Existing records: "
        f"{existing_record_count}"
    )

    print(
        f"Collected at: "
        f"{collected_at}"
    )

    with OUTPUT_FILE.open(
        "a",
        encoding="utf-8",
    ) as output:

        if args.off_file is not None:

            off_file = (
                args.off_file.resolve()
            )

            if not off_file.exists():

                raise FileNotFoundError(
                    "Open Food Facts file "
                    "not found: "
                    f"{off_file}"
                )

            print()
            print(
                "Processing "
                "Open Food Facts..."
            )

            snapshot_sha256 = (
                sha256_file(
                    off_file
                )
            )

            for product in (
                parse_open_food_facts(
                    file_path=off_file,
                    snapshot_sha256=(
                        snapshot_sha256
                    ),
                    collected_at=(
                        collected_at
                    ),
                    limit=(
                        args.off_limit
                    ),
                )
            ):

                dedup_key = (
                    product.source_name,
                    product.barcode,
                )

                if dedup_key in (
                    seen_records
                ):
                    continue

                seen_records.add(
                    dedup_key
                )

                write_product(
                    output,
                    product,
                )

                total_written += 1

                source_counts[
                    "Open Food Facts"
                ] += 1

        if (
            args.openlibrary_file
            is not None
        ):

            openlibrary_file = (
                args.openlibrary_file.resolve()
            )

            if not (
                openlibrary_file.exists()
            ):

                raise FileNotFoundError(
                    "Open Library file "
                    "not found: "
                    f"{openlibrary_file}"
                )

            print()
            print(
                "Processing "
                "Open Library..."
            )

            snapshot_sha256 = (
                sha256_file(
                    openlibrary_file
                )
            )

            for product in (
                parse_open_library(
                    file_path=(
                        openlibrary_file
                    ),
                    snapshot_sha256=(
                        snapshot_sha256
                    ),
                    collected_at=(
                        collected_at
                    ),
                    limit=(
                        args.openlibrary_limit
                    ),
                )
            ):

                dedup_key = (
                    product.source_name,
                    product.barcode,
                )

                if dedup_key in (
                    seen_records
                ):
                    continue

                seen_records.add(
                    dedup_key
                )

                write_product(
                    output,
                    product,
                )

                total_written += 1

                source_counts[
                    "Open Library"
                ] += 1

    print()
    print("=" * 80)
    print(
        "BULK EXTRACTION COMPLETE"
    )
    print("=" * 80)

    print(
        f"Existing records: "
        f"{existing_record_count}"
    )

    print(
        f"New records added: "
        f"{total_written}"
    )

    print(
        f"Total records now: "
        f"{existing_record_count + total_written}"
    )

    for (
        source_name,
        count,
    ) in source_counts.items():

        print(
            f"{source_name} "
            f"new records: "
            f"{count}"
        )

    print(
        f"Output file: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()