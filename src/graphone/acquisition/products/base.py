from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RawProductRecord:
    """
    A raw product record returned by a real external source.

    The raw payload is preserved rather than generated
    or completed by GraphOne.
    """

    source_id: str

    source_name: str

    source_url: str

    raw_data: dict


class ProductSourceConnector(ABC):
    """
    Common interface for all product acquisition sources.

    Every connector must:

    - acquire records from a real source
    - preserve the source URL
    - return source-derived raw data
    - avoid LLM-generated values

    Connectors may implement their own pagination,
    retries, rate limiting, or bulk-download logic.
    """

    SOURCE_ID: str

    SOURCE_NAME: str

    @abstractmethod
    async def acquire(
        self,
        target_count: int,
    ) -> list[RawProductRecord]:
        """
        Acquire up to target_count raw records.

        Records returned here must originate directly
        from the external source.
        """

        raise NotImplementedError