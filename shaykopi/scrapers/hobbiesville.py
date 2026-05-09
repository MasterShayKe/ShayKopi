"""Hobbiesville (Canada, Shopify, CAD store)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..models import Site
from ._shopify import walk_shopify
from .base import BaseScraper, RawListing


class HobbiesvilleScraper(BaseScraper):
    site = Site.HOBBIESVILLE
    base_url = "https://hobbiesville.com"
    store_currency = "CAD"

    async def scan(self, *, limit: int | None = None) -> AsyncIterator[RawListing]:
        async for listing in walk_shopify(
            self.base_url,
            site=self.site,
            store_currency=self.store_currency,
            limit=limit,
        ):
            yield listing
