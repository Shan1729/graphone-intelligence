from __future__ import annotations

import asyncio

from graphone.acquisition.products.base import (
    ProductSourceConnector,
    RawProductRecord,
)


class ProductAcquisitionCoordinator:
    """
    Coordinates acquisition across multiple product sources.

    The coordinator does not know how individual sources
    fetch data. Each source is represented by a connector
    implementing ProductSourceConnector.

    Responsibilities:

    - select enabled connectors
    - allocate acquisition targets
    - execute connectors
    - isolate source failures
    - combine source-derived records

    It does not:

    - generate product records
    - infer missing source data
    - modify raw source records
    - use an LLM
    """

    def __init__(
        self,
        connectors: list[
            ProductSourceConnector
        ],
    ) -> None:

        if not connectors:
            raise ValueError(
                "At least one product source "
                "connector is required"
            )

        self.connectors = list(
            connectors
        )

    async def acquire(
        self,
        target_count: int,
    ) -> list[RawProductRecord]:
        """
        Acquire records from all registered sources.

        Acquisition failures from one source do not
        automatically stop successful acquisition from
        other sources.
        """

        if target_count < 1:
            raise ValueError(
                "target_count must be >= 1"
            )

        connector_count = len(
            self.connectors
        )

        # Each connector receives an approximately equal
        # target. Sources may return fewer records.
        base_target = (
            target_count // connector_count
        )

        remainder = (
            target_count % connector_count
        )

        targets: list[int] = []

        for index in range(
            connector_count
        ):

            connector_target = (
                base_target
            )

            if index < remainder:
                connector_target += 1

            targets.append(
                connector_target
            )

        async def acquire_from_connector(
            connector: ProductSourceConnector,
            connector_target: int,
        ) -> list[RawProductRecord]:

            try:

                return await connector.acquire(
                    target_count=connector_target
                )

            except Exception:

                # Source failure isolation:
                # other sources may still succeed.
                return []

        tasks = [
            acquire_from_connector(
                connector=connector,
                connector_target=connector_target,
            )

            for (
                connector,
                connector_target,
            ) in zip(
                self.connectors,
                targets,
            )
        ]

        results = await asyncio.gather(
            *tasks
        )

        records: list[
            RawProductRecord
        ] = []

        for source_records in results:

            records.extend(
                source_records
            )

            if len(records) >= target_count:
                break

        return records[:target_count]