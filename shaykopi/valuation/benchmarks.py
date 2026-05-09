"""Maintain per-card price benchmarks."""

from __future__ import annotations

import statistics
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Benchmark, BenchmarkType, CanonicalCard, Listing, Site, SoldComp

BENCHMARK_FRESHNESS = timedelta(hours=24)


def get_or_compute_cross_site_min(
    sess: Session, canonical_id: int, *, exclude_listing_id: int | None = None
) -> Benchmark | None:
    """Lowest current asking price for a canonical card across all sites."""
    stmt = select(Listing).where(
        Listing.canonical_card_id == canonical_id,
        Listing.is_active == True,  # noqa: E712
    )
    if exclude_listing_id is not None:
        stmt = stmt.where(Listing.id != exclude_listing_id)
    listings = sess.scalars(stmt).all()
    if len(listings) < 2:
        return None
    min_price = min(listing.price_usd for listing in listings)
    bench = sess.scalar(
        select(Benchmark).where(
            Benchmark.canonical_card_id == canonical_id,
            Benchmark.benchmark_type == BenchmarkType.CROSS_SITE_MIN,
        )
    )
    now = datetime.now(UTC)
    if bench is None:
        bench = Benchmark(
            canonical_card_id=canonical_id,
            benchmark_type=BenchmarkType.CROSS_SITE_MIN,
            value_usd=min_price,
            sample_size=len(listings),
            as_of=now,
        )
        sess.add(bench)
    else:
        bench.value_usd = min_price
        bench.sample_size = len(listings)
        bench.as_of = now
    return bench


def get_tcgplayer_market(sess: Session, canonical_id: int) -> Benchmark | None:
    return sess.scalar(
        select(Benchmark).where(
            Benchmark.canonical_card_id == canonical_id,
            Benchmark.benchmark_type == BenchmarkType.TCGPLAYER_MARKET,
        )
    )


def recompute_ebay_sold_median(
    sess: Session, canonical_id: int, *, lookback_days: int = 30
) -> Benchmark | None:
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    rows = sess.scalars(
        select(SoldComp).where(
            SoldComp.canonical_card_id == canonical_id,
            SoldComp.site == Site.EBAY,
            SoldComp.sold_at >= cutoff,
        )
    ).all()
    if len(rows) < 3:
        return None
    median = statistics.median(row.sold_price_usd for row in rows)

    bench = sess.scalar(
        select(Benchmark).where(
            Benchmark.canonical_card_id == canonical_id,
            Benchmark.benchmark_type == BenchmarkType.EBAY_SOLD_MEDIAN,
        )
    )
    now = datetime.now(UTC)
    if bench is None:
        bench = Benchmark(
            canonical_card_id=canonical_id,
            benchmark_type=BenchmarkType.EBAY_SOLD_MEDIAN,
            value_usd=median,
            sample_size=len(rows),
            as_of=now,
        )
        sess.add(bench)
    else:
        bench.value_usd = median
        bench.sample_size = len(rows)
        bench.as_of = now
    return bench


def best_benchmark_for(sess: Session, card: CanonicalCard, *, exclude_listing_id: int | None = None
) -> Benchmark | None:
    """Pick the strongest benchmark available — sold > market > cross-site."""
    candidates = []
    sold = sess.scalar(
        select(Benchmark).where(
            Benchmark.canonical_card_id == card.id,
            Benchmark.benchmark_type == BenchmarkType.EBAY_SOLD_MEDIAN,
        )
    )
    if sold and sold.sample_size >= 3:
        candidates.append(sold)
    market = get_tcgplayer_market(sess, card.id)
    if market:
        candidates.append(market)
    cross = get_or_compute_cross_site_min(
        sess, card.id, exclude_listing_id=exclude_listing_id
    )
    if cross:
        candidates.append(cross)
    return candidates[0] if candidates else None
