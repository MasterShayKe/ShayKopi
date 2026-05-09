"""eBay sold-comp fetcher.

Hits the public ``/sch/i.html?...&LH_Sold=1&LH_Complete=1`` page and parses
out recent sold prices. Used to build the EBAY_SOLD_MEDIAN benchmark for a
canonical card. Cache aggressively (24h) to avoid hammering the page.

Returns a list of ``(price_usd, sold_at, title)`` tuples.
"""

from __future__ import annotations

import contextlib
import logging
import re
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from selectolax.parser import HTMLParser

from ..config import get_settings

log = logging.getLogger(__name__)

SEARCH_URL = "https://www.ebay.com/sch/i.html"

_PRICE_RE = re.compile(r"\$?\s*([\d,]+\.\d{2})")
_DATE_RE = re.compile(r"Sold\s+(?:on\s+)?([A-Za-z]{3}\s+\d{1,2},?\s+\d{4})")


async def fetch_sold_comps(query: str, *, max_results: int = 60) -> list[tuple[float, datetime, str]]:
    settings = get_settings()
    params = {
        "_nkw": query,
        "LH_Sold": "1",
        "LH_Complete": "1",
        "_ipg": min(240, max_results),
    }
    url = f"{SEARCH_URL}?{urlencode(params)}"
    headers = {
        "User-Agent": settings.user_agent,
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, headers=headers) as client:
        r = await client.get(url)
        r.raise_for_status()
        html = r.text

    tree = HTMLParser(html)
    out: list[tuple[float, datetime, str]] = []
    for item in tree.css("li.s-item"):
        title_el = item.css_first(".s-item__title")
        price_el = item.css_first(".s-item__price")
        date_el = item.css_first(".s-item__caption .s-item__caption--signal") or item.css_first(
            ".s-item__title--tagblock"
        )
        if not title_el or not price_el:
            continue
        title = title_el.text(strip=True)
        if title.lower().startswith("shop on ebay"):
            continue
        m = _PRICE_RE.search(price_el.text())
        if not m:
            continue
        price = float(m.group(1).replace(",", ""))
        sold_at = datetime.now(UTC) - timedelta(days=14)
        if date_el:
            md = _DATE_RE.search(date_el.text())
            if md:
                with contextlib.suppress(ValueError):
                    sold_at = datetime.strptime(md.group(1).replace(",", ""), "%b %d %Y").replace(
                        tzinfo=UTC
                    )
        out.append((price, sold_at, title))
        if len(out) >= max_results:
            break
    return out
