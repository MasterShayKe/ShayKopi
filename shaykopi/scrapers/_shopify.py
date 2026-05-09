"""Shared Shopify ``/products.json`` walker.

Most TCG retailers run Shopify and expose every active product (with all
variants and prices) under ``/products.json?page=N&limit=250`` with no auth
needed. We use this for Hobbiesville and GameNerds.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import get_settings
from ..models import Site
from .base import RawListing

log = logging.getLogger(__name__)

# CAD->USD fallback when a Shopify store reports CAD; the official Shopify
# product endpoint doesn't expose currency per product, so we infer from the
# store's domain / config and let the caller pin it.
_FX_FALLBACK = {"CAD": 0.73, "GBP": 1.27, "EUR": 1.08}


async def walk_shopify(
    base_url: str,
    *,
    site: Site,
    store_currency: str = "USD",
    fx_rate_to_usd: float | None = None,
    limit: int | None = None,
    page_size: int = 250,
) -> AsyncIterator[RawListing]:
    """Yield every variant of every product as a RawListing.

    `fx_rate_to_usd` overrides the static fallback if the caller has a fresher
    rate.  Default behavior: identity for USD stores, fallback table otherwise.
    """
    settings = get_settings()
    headers = {"User-Agent": settings.user_agent, "Accept": "application/json"}
    fx = 1.0 if store_currency == "USD" else (fx_rate_to_usd or _FX_FALLBACK.get(store_currency, 1.0))

    yielded = 0
    page = 1
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, headers=headers) as client:
        while True:
            url = f"{base_url.rstrip('/')}/products.json"
            params = {"page": page, "limit": page_size}

            async for attempt in AsyncRetrying(
                wait=wait_exponential(multiplier=1, min=1, max=10),
                stop=stop_after_attempt(4),
                retry=retry_if_exception_type((httpx.HTTPError,)),
                reraise=True,
            ):
                with attempt:
                    r = await client.get(url, params=params)
                    r.raise_for_status()

            payload = r.json()
            products = payload.get("products", []) or []
            if not products:
                break

            for product in products:
                handle = product.get("handle")
                title = product.get("title", "")
                product_url = f"{base_url.rstrip('/')}/products/{handle}" if handle else base_url
                image = (product.get("images") or [{}])[0].get("src") if product.get("images") else None
                for variant in product.get("variants", []) or []:
                    if not variant.get("available", True):
                        continue
                    price_str = variant.get("price")
                    if not price_str:
                        continue
                    try:
                        price = float(price_str) * fx
                    except (TypeError, ValueError):
                        continue
                    variant_title = variant.get("title") or ""
                    full_title = title if variant_title in ("", "Default Title") else f"{title} — {variant_title}"
                    yield RawListing(
                        site=site,
                        external_id=str(variant.get("id")),
                        url=product_url,
                        title=full_title,
                        price_usd=round(price, 2),
                        currency="USD",
                        condition=None,
                        grade=None,
                        image_url=image,
                        raw={"product_id": product.get("id"), "variant_id": variant.get("id")},
                    )
                    yielded += 1
                    if limit is not None and yielded >= limit:
                        return

            if len(products) < page_size:
                break
            page += 1
