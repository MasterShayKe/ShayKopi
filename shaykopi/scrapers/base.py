"""Common scraper contract.

Every scraper emits a stream of `RawListing` records. A separate persist step
turns them into rows in `listings`. Keep scrapers stateless and side-effect
free so they're easy to test against recorded fixtures.
"""

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from dataclasses import dataclass

from ..models import Site


@dataclass(frozen=True)
class RawListing:
    site: Site
    external_id: str
    url: str
    title: str
    price_usd: float
    currency: str = "USD"
    condition: str | None = None
    grade: str | None = None
    image_url: str | None = None
    raw: dict | None = None


class BaseScraper(abc.ABC):
    site: Site

    @abc.abstractmethod
    async def scan(self, *, limit: int | None = None) -> AsyncIterator[RawListing]:
        """Yield listings until the source is exhausted or `limit` reached."""
        if False:  # pragma: no cover  - typing helper
            yield  # type: ignore[misc]
