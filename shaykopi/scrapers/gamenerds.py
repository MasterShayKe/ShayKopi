"""GameNerds (USA, Shopify)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..models import Site
from ._shopify import walk_shopify
from .base import BaseScraper, RawListing


class GameNerdsScraper(BaseScraper):
    site = Site.GAMENERDS
    base_url = "https://thegamenerds.com"
    store_currency = "USD"

    async def scan(self, *, limit: int | None = None) -> AsyncIterator[RawListing]:
        async for listing in walk_shopify(
            self.base_url,
            site=self.site,
            store_currency=self.store_currency,
            limit=limit,
        ):
            yield listing
