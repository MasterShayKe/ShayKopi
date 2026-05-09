"""eBay scraper.

Uses the official Browse API (`/buy/browse/v1/item_summary/search`) with an
``EBAY_APP_ID`` (free developer key) for active listings. Sold-comp scraping
is delegated to a separate helper because it hits the public web search and
should be cached aggressively.
"""

from __future__ import annotations

import base64
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx

from ..config import get_settings
from ..models import Site
from .base import BaseScraper, RawListing

log = logging.getLogger(__name__)

OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"


class EbayScraper(BaseScraper):
    site = Site.EBAY

    def __init__(self, queries: list[str] | None = None) -> None:
        # Default queries cover both games and several flavors of inventory.
        self.queries = queries or [
            "pokemon tcg sealed booster box",
            "pokemon tcg etb",
            "pokemon tcg charizard",
            "one piece tcg booster box",
            "one piece tcg leader",
        ]
        self._token: str | None = None
        self._token_expires: datetime | None = None

    async def _get_app_token(self, client: httpx.AsyncClient) -> str | None:
        """eBay Browse API needs an OAuth client_credentials token."""
        if self._token and self._token_expires and self._token_expires > datetime.now(UTC):
            return self._token

        settings = get_settings()
        # ``ebay_app_id`` is expected to be ``CLIENT_ID:CLIENT_SECRET`` for
        # simplicity; if only the AppID is set we cannot mint a token and the
        # caller should fall back to authless endpoints.
        if not settings.ebay_app_id or ":" not in settings.ebay_app_id:
            return None
        basic = base64.b64encode(settings.ebay_app_id.encode()).decode()
        r = await client.post(
            OAUTH_URL,
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
        )
        r.raise_for_status()
        body = r.json()
        self._token = body["access_token"]
        self._token_expires = datetime.now(UTC) + timedelta(seconds=body["expires_in"] - 60)
        return self._token

    async def scan(self, *, limit: int | None = None) -> AsyncIterator[RawListing]:
        settings = get_settings()
        headers = {"User-Agent": settings.user_agent}

        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, headers=headers) as client:
            token = await self._get_app_token(client)
            if not token:
                log.warning("EBAY_APP_ID missing or malformed; skipping eBay scan.")
                return

            yielded = 0
            for q in self.queries:
                params = {
                    "q": q,
                    "limit": min(200, limit or 200),
                    "filter": "buyingOptions:{FIXED_PRICE},priceCurrency:USD",
                    "sort": "newlyListed",
                }
                r = await client.get(
                    BROWSE_URL,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-EBAY-C-MARKETPLACE-ID": settings.ebay_marketplace,
                    },
                )
                r.raise_for_status()
                items = (r.json() or {}).get("itemSummaries", []) or []
                for it in items:
                    price_obj = it.get("price") or {}
                    try:
                        price = float(price_obj.get("value"))
                    except (TypeError, ValueError):
                        continue
                    yield RawListing(
                        site=self.site,
                        external_id=it["itemId"],
                        url=it.get("itemWebUrl", ""),
                        title=it.get("title", ""),
                        price_usd=price,
                        currency=price_obj.get("currency", "USD"),
                        condition=it.get("condition"),
                        grade=None,
                        image_url=(it.get("image") or {}).get("imageUrl"),
                        raw={"query": q, "categories": it.get("categories")},
                    )
                    yielded += 1
                    if limit is not None and yielded >= limit:
                        return
