"""TCGPlayer scraper.

There is no public TCGPlayer API without partner approval. We *price* via
``pokemontcg.io`` and ``apitcg.com`` (handled by the catalog seeders), and
treat TCGPlayer as primarily a *benchmark* source rather than an active-
listing source.

This scraper is therefore a thin wrapper that emits zero RawListings today
but keeps the slot reserved so the dashboard, scheduler, and Site enum
remain consistent. Phase 4 of the roadmap adds Playwright-based scraping
of the search page to capture under-priced direct-from-seller listings.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..models import Site
from .base import BaseScraper, RawListing


class TCGPlayerScraper(BaseScraper):
    site = Site.TCGPLAYER

    async def scan(self, *, limit: int | None = None) -> AsyncIterator[RawListing]:
        # Reserved for the Playwright-based active-listing scraper. For now
        # the integration is benchmark-only via the catalog seeders.
        return
        yield  # pragma: no cover  - typing
