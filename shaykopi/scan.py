"""Run a single scan cycle: scrape -> persist -> evaluate -> alert."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from .alerts.dispatcher import dispatch_new_deals
from .db import session_scope
from .models import Listing, Site
from .scrapers import BaseScraper
from .scrapers.ebay import EbayScraper
from .scrapers.gamenerds import GameNerdsScraper
from .scrapers.hobbiesville import HobbiesvilleScraper
from .scrapers.persist import upsert_listing
from .scrapers.tcgplayer import TCGPlayerScraper
from .valuation.engine import evaluate_listing

log = logging.getLogger(__name__)

ALL_SCRAPERS: list[type[BaseScraper]] = [
    HobbiesvilleScraper,
    GameNerdsScraper,
    TCGPlayerScraper,
    EbayScraper,
]


async def _run_one(scraper: BaseScraper, *, limit: int | None) -> int:
    count = 0
    listing_ids: list[int] = []
    async for raw in scraper.scan(limit=limit):
        with session_scope() as sess:
            listing = upsert_listing(sess, raw)
            listing_ids.append(listing.id)
            count += 1
    # Evaluate after persisting so cross-site benchmarks are accurate.
    with session_scope() as sess:
        listings = sess.scalars(select(Listing).where(Listing.id.in_(listing_ids))).all()
        for listing in listings:
            evaluate_listing(sess, listing)
    return count


def expire_stale_listings(max_age_hours: int = 24) -> int:
    cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
    with session_scope() as sess:
        result = sess.execute(
            update(Listing)
            .where(Listing.is_active == True, Listing.last_seen < cutoff)  # noqa: E712
            .values(is_active=False)
        )
        return result.rowcount or 0


async def run_scan(*, sites: list[Site] | None = None, limit: int | None = None) -> dict:
    sites_to_run = sites or [s.value for s in Site]  # type: ignore[list-item]
    summary: dict[str, int] = {}
    for cls in ALL_SCRAPERS:
        if cls.site not in sites_to_run and cls.site.value not in sites_to_run:
            continue
        try:
            n = await _run_one(cls(), limit=limit)
            summary[cls.site.value] = n
            log.info("scan %s: %d listings", cls.site.value, n)
        except Exception:
            log.exception("scan %s failed", cls.site.value)
            summary[cls.site.value] = -1
    expired = expire_stale_listings()
    summary["_expired"] = expired

    with session_scope() as sess:
        alerted = await dispatch_new_deals(sess)
    summary["_alerted"] = alerted
    return summary


def run_scan_sync(**kwargs) -> dict:
    return asyncio.run(run_scan(**kwargs))
