from __future__ import annotations

from pathlib import Path

from graphone.retrieval.base_searcher import (
    DeterministicJSONLSearcher,
)


class ProductSearcher(
    DeterministicJSONLSearcher,
):
    """
    Deterministic searcher for acquired GraphOne
    product records.

    Uses only stored product evidence.

    No LLM is used for retrieval.

    No external data is acquired.

    No records are generated, inferred, or modified.
    """

    DATASET_NAME = (
        "products"
    )

    RECORD_ID_PREFIX = (
        "product"
    )

    SEARCHABLE_FIELDS = (
        "product_name",
        "brand",
        "description",
        "category",
        "quantity",
    )

    FIELD_WEIGHTS = {
        "product_name": 5,
        "brand": 4,
        "category": 3,
        "description": 2,
        "quantity": 1,
    }

    # These words describe the dataset itself.
    #
    # They should not be required to exist inside
    # every individual product record.
    DATASET_STOPWORDS = {
        "product",
        "products",
        "item",
        "items",
        "find",
        "show",
        "me",
        "about",
        "the",
        "a",
        "an",
    }

    # Explicit deterministic retrieval aliases.
    #
    # These aliases do not generate or infer records.
    QUERY_ALIASES = {
        "chocolate": {
            "chocolate",
            "cocoa",
        },
        "soda": {
            "soda",
            "soft drink",
            "softdrink",
        },
        "juice": {
            "juice",
            "fruit juice",
        },
        "yogurt": {
            "yogurt",
            "yoghurt",
            "iogurte",
        },
    }

    def __init__(
        self,
        file_path: Path | str,
    ) -> None:

        super().__init__(
            file_path=file_path,
        )

    def _is_valid_record(
        self,
        record: dict,
    ) -> bool:
        """
        Product-specific structural validation.

        A valid product must contain:

        - record_type = PRODUCT
        - product_name
        - barcode
        - product_url

        Provenance validation is handled by the
        DeterministicJSONLSearcher when creating
        EvidenceRecord objects.
        """

        if (
            record.get(
                "record_type"
            )
            != "PRODUCT"
        ):
            return False

        product_name = record.get(
            "product_name"
        )

        barcode = record.get(
            "barcode"
        )

        product_url = record.get(
            "product_url"
        )

        return (
            isinstance(
                product_name,
                str,
            )
            and bool(
                product_name.strip()
            )
            and isinstance(
                barcode,
                str,
            )
            and bool(
                barcode.strip()
            )
            and isinstance(
                product_url,
                str,
            )
            and bool(
                product_url.strip()
            )
        )