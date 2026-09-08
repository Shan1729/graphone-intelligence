from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductSource:
    """
    Immutable metadata describing one product source.

    This registry describes acquisition sources only.
    It does not retrieve or generate product records.
    """

    source_id: str

    source_name: str

    base_url: str

    record_type: str

    enabled: bool = True


PRODUCT_SOURCES: tuple[
    ProductSource,
    ...,
] = (
    ProductSource(
        source_id="openfoodfacts",
        source_name="Open Food Facts",
        base_url=(
            "https://world.openfoodfacts.org"
        ),
        record_type="PRODUCT",
        enabled=True,
    ),
)