from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

from graphone.acquisition.cas import store_snapshot
from graphone.storage.db import init_db, record_acquisition


OPEN_FOOD_FACTS_SEARCH_URL = (
    "https://world.openfoodfacts.org/api/v2/search"
)

PAGE_SIZE = 100


@dataclass(frozen=True)
class Product:
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


class OpenFoodFactsProductExtractor:
    """
    Deterministic bulk extractor for real product records.

    Products are acquired directly from the Open Food Facts API.
    No LLM is used to generate, infer, or complete product data.
    """

    def __init__(
        self,
        page_size: int = PAGE_SIZE,
        timeout: float = 60.0,
        max_retries: int = 8,
    ) -> None:
        if page_size < 1:
            raise ValueError(
                "page_size must be >= 1"
            )

        if max_retries < 0:
            raise ValueError(
                "max_retries must be >= 0"
            )

        self.page_size = page_size
        self.timeout = timeout
        self.max_retries = max_retries

    @staticmethod
    def _normalize_text(
        value: object,
    ) -> str | None:
        """
        Deterministically normalize source text.

        No new content is generated.
        """

        if not isinstance(value, str):
            return None

        value = " ".join(
            value.split()
        )

        return value or None

    @staticmethod
    def _is_valid_http_url(
        value: object,
    ) -> bool:
        if not isinstance(value, str):
            return False

        value = value.strip()

        if not value:
            return False

        try:
            parsed = urlsplit(value)
        except ValueError:
            return False

        return (
            parsed.scheme
            in {"http", "https"}
            and bool(parsed.netloc)
            and bool(parsed.hostname)
        )

    @staticmethod
    def _retry_delay(
        attempt: int,
        response: httpx.Response | None = None,
    ) -> int:
        """
        Determine retry delay.

        Uses Retry-After when supplied by the
        source. Otherwise uses deterministic
        exponential backoff.
        """

        if response is not None:
            retry_after = (
                response.headers.get(
                    "Retry-After"
                )
            )

            if (
                retry_after
                and retry_after.isdigit()
            ):
                return min(
                    60,
                    int(retry_after),
                )

        return min(
            60,
            5 * (2 ** attempt),
        )

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        page: int,
    ) -> tuple[bytes, str]:
        """
        Fetch one real Open Food Facts search page.

        Temporary rate-limit and server failures
        are retried with deterministic backoff.
        """

        params = {
            "page": page,
            "page_size": self.page_size,
            "fields": (
                "code,"
                "product_name,"
                "brands,"
                "categories,"
                "quantity,"
                "url"
            ),
        }

        headers = {
            "User-Agent": (
                "GraphOneIntelligence/1.0 "
                "(educational-project; "
                "bulk-data-acquisition)"
            ),
            "Accept": "application/json",
        }

        last_error: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                response = await client.get(
                    OPEN_FOOD_FACTS_SEARCH_URL,
                    params=params,
                    headers=headers,
                )

                is_retryable_status = (
                    response.status_code == 429
                    or response.status_code >= 500
                )

                if is_retryable_status:
                    last_error = RuntimeError(
                        f"HTTP "
                        f"{response.status_code}"
                    )

                    if attempt < self.max_retries:
                        wait_seconds = (
                            self._retry_delay(
                                attempt,
                                response,
                            )
                        )

                        print(
                            f"Page {page}: HTTP "
                            f"{response.status_code}. "
                            f"Retry "
                            f"{attempt + 1}/"
                            f"{self.max_retries}. "
                            f"Waiting "
                            f"{wait_seconds} seconds..."
                        )

                        await asyncio.sleep(
                            wait_seconds
                        )

                        continue

                response.raise_for_status()

                return (
                    response.content,
                    str(response.url),
                )

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPError,
                RuntimeError,
            ) as exc:

                last_error = exc

                if attempt < self.max_retries:
                    wait_seconds = (
                        self._retry_delay(
                            attempt
                        )
                    )

                    print(
                        f"Page {page}: "
                        f"{type(exc).__name__}. "
                        f"Retry "
                        f"{attempt + 1}/"
                        f"{self.max_retries}. "
                        f"Waiting "
                        f"{wait_seconds} seconds..."
                    )

                    await asyncio.sleep(
                        wait_seconds
                    )

        raise RuntimeError(
            f"Failed to fetch product page "
            f"{page} after "
            f"{self.max_retries + 1} attempts: "
            f"{last_error}"
        )

    def _parse_product(
        self,
        raw_product: object,
        source_url: str,
        snapshot_sha256: str,
        collected_at: str,
    ) -> Product | None:
        """
        Parse only values supplied by the source.

        Invalid or incomplete records are skipped.
        No fields are generated or repaired.
        """

        if not isinstance(
            raw_product,
            dict,
        ):
            return None

        barcode = self._normalize_text(
            raw_product.get("code")
        )

        product_name = self._normalize_text(
            raw_product.get(
                "product_name"
            )
        )

        product_url = self._normalize_text(
            raw_product.get("url")
        )

        if (
            not barcode
            or not product_name
        ):
            return None

        if not self._is_valid_http_url(
            product_url
        ):
            return None

        return Product(
            schema_version="1.0",
            record_type="PRODUCT",
            source_name="Open Food Facts",
            source_url=source_url,
            product_name=product_name,
            product_url=product_url,
            barcode=barcode,
            brand=self._normalize_text(
                raw_product.get("brands")
            ),
            description=None,
            category=self._normalize_text(
                raw_product.get(
                    "categories"
                )
            ),
            quantity=self._normalize_text(
                raw_product.get(
                    "quantity"
                )
            ),
            raw_snapshot_sha256=(
                snapshot_sha256
            ),
            collected_at=collected_at,
        )

    async def extract(
        self,
        target_count: int = 1000,
    ) -> list[Product]:
        """
        Extract up to target_count unique real products.

        Every returned product originates from
        the Open Food Facts API.
        """

        if target_count < 1:
            raise ValueError(
                "target_count must be >= 1"
            )

        init_db()

        products: list[Product] = []
        seen_barcodes: set[str] = set()

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:

            page = 1

            while (
                len(products)
                < target_count
            ):
                content, final_url = (
                    await self._fetch_page(
                        client=client,
                        page=page,
                    )
                )

                snapshot = store_snapshot(
                    content=content,
                    source_url=final_url,
                    content_type=(
                        "application/json"
                    ),
                )

                collected_at = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                record_acquisition(
                    sha256=snapshot.sha256,
                    source_url=final_url,
                    created_at=(
                        collected_at
                    ),
                )

                payload = json.loads(
                    content.decode("utf-8")
                )

                raw_products = (
                    payload.get(
                        "products",
                        [],
                    )
                )

                if (
                    not isinstance(
                        raw_products,
                        list,
                    )
                    or not raw_products
                ):
                    break

                for raw_product in raw_products:
                    product = (
                        self._parse_product(
                            raw_product=(
                                raw_product
                            ),
                            source_url=(
                                final_url
                            ),
                            snapshot_sha256=(
                                snapshot.sha256
                            ),
                            collected_at=(
                                collected_at
                            ),
                        )
                    )

                    if product is None:
                        continue

                    if (
                        product.barcode
                        in seen_barcodes
                    ):
                        continue

                    seen_barcodes.add(
                        product.barcode
                    )

                    products.append(
                        product
                    )

                    if (
                        len(products)
                        >= target_count
                    ):
                        break

                if (
                    len(products)
                    >= target_count
                ):
                    break

                page += 1

                # Respectful pacing between
                # consecutive bulk API requests.
                await asyncio.sleep(6)

        return products[:target_count]