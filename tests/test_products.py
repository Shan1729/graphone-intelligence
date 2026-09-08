import pytest

from graphone.extraction.products import (
    OpenFoodFactsProductExtractor,
)


@pytest.mark.asyncio
async def test_extract_real_products():
    extractor = OpenFoodFactsProductExtractor(
        page_size=100,
        timeout=60.0,
        max_retries=2,
    )

    products = await extractor.extract(
        target_count=5,
    )

    assert len(products) == 5

    barcodes = set()

    for product in products:
        assert product.schema_version == "1.0"
        assert product.record_type == "PRODUCT"
        assert product.source_name == "Open Food Facts"

        assert product.source_url.startswith(
            ("http://", "https://")
        )

        assert product.product_name
        assert product.product_url.startswith(
            ("http://", "https://")
        )

        assert product.barcode
        assert len(
            product.raw_snapshot_sha256
        ) == 64

        assert product.collected_at

        barcodes.add(
            product.barcode
        )

    assert len(barcodes) == 5