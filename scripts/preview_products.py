import asyncio

from graphone.extraction.products import (
    OpenFoodFactsProductExtractor,
)


async def main():
    extractor = OpenFoodFactsProductExtractor(
        page_size=100,
        timeout=60.0,
        max_retries=2,
    )

    products = await extractor.extract(
        target_count=5,
    )

    for index, product in enumerate(
        products,
        start=1,
    ):
        print("\n" + "=" * 80)
        print(f"PRODUCT {index}")
        print("=" * 80)
        print(f"Name: {product.product_name}")
        print(f"Barcode: {product.barcode}")
        print(f"Product URL: {product.product_url}")
        print(f"Brand: {product.brand}")
        print(f"Category: {product.category}")
        print(f"Quantity: {product.quantity}")
        print(f"Source: {product.source_name}")
        print(f"Source URL: {product.source_url}")
        print(
            f"Snapshot SHA-256: "
            f"{product.raw_snapshot_sha256}"
        )
        print(f"Collected At: {product.collected_at}")


if __name__ == "__main__":
    asyncio.run(main())