"""Decide whether a listing is a deal and create/refresh a Deal row.

A listing is a deal when:
    price <= benchmark * (1 - DEAL_MARGIN_PCT)  AND
    benchmark >= DEAL_MIN_BENCHMARK_USD

Profit estimate = sale_price * (1 - WHATNOT_FEE_PCT) - SHIPPING - cost
For sale_price we conservatively use the same benchmark.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Deal, DealStatus, Listing
from .benchmarks import best_benchmark_for

log = logging.getLogger(__name__)


def _profit(sale_price: float, cost: float) -> float:
    settings = get_settings()
    return round(
        sale_price * (1 - settings.whatnot_fee_pct) - settings.shipping_cost_usd - cost, 2
    )


def evaluate_listing(sess: Session, listing: Listing) -> Deal | None:
    """Create or update a Deal row for `listing` if it qualifies."""
    settings = get_settings()
    if listing.canonical is None or not listing.is_active:
        return None

    bench = best_benchmark_for(sess, listing.canonical, exclude_listing_id=listing.id)
    if bench is None or bench.value_usd < settings.deal_min_benchmark_usd:
        return None

    margin = 1 - (listing.price_usd / bench.value_usd) if bench.value_usd > 0 else 0
    if margin < settings.deal_margin_pct:
        # No longer a deal — close any existing NEW/ALERTED deal as expired.
        existing = sess.scalar(select(Deal).where(Deal.listing_id == listing.id))
        if existing and existing.status in {DealStatus.NEW, DealStatus.ALERTED}:
            existing.status = DealStatus.EXPIRED
        return None

    estimated_profit = _profit(bench.value_usd, listing.price_usd)
    existing = sess.scalar(select(Deal).where(Deal.listing_id == listing.id))
    if existing is None:
        deal = Deal(
            listing_id=listing.id,
            benchmark_type=bench.benchmark_type,
            benchmark_value_usd=bench.value_usd,
            margin_pct=round(margin, 4),
            estimated_profit_usd=estimated_profit,
            status=DealStatus.NEW,
        )
        sess.add(deal)
        sess.flush()
        return deal

    existing.benchmark_type = bench.benchmark_type
    existing.benchmark_value_usd = bench.value_usd
    existing.margin_pct = round(margin, 4)
    existing.estimated_profit_usd = estimated_profit
    if existing.status == DealStatus.EXPIRED:
        existing.status = DealStatus.NEW
    return existing


def evaluate_many(sess: Session, listings: Iterable[Listing]) -> list[Deal]:
    deals: list[Deal] = []
    for listing in listings:
        d = evaluate_listing(sess, listing)
        if d is not None:
            deals.append(d)
    return deals
