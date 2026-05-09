"""Tests for the valuation engine + benchmarks."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from shaykopi.config import get_settings
from shaykopi.models import (
    Base,
    Benchmark,
    BenchmarkType,
    CanonicalCard,
    DealStatus,
    Game,
    Listing,
    Site,
)
from shaykopi.valuation.engine import evaluate_listing


@pytest.fixture()
def session(monkeypatch):
    # In-memory SQLite, isolated per test
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Sess = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    s = Sess()
    yield s
    s.close()


def _seed(sess, *, market_price: float):
    card = CanonicalCard(
        game=Game.POKEMON, set_code="sv3pt5", number="199", name="Charizard ex", variant="normal"
    )
    sess.add(card)
    sess.flush()
    sess.add(
        Benchmark(
            canonical_card_id=card.id,
            benchmark_type=BenchmarkType.TCGPLAYER_MARKET,
            value_usd=market_price,
            sample_size=1,
            as_of=datetime.now(UTC),
        )
    )
    sess.flush()
    return card


def _make_listing(sess, card, *, price: float, ext: str = "abc"):
    listing = Listing(
        site=Site.HOBBIESVILLE,
        external_id=ext,
        url="https://example.com/p/x",
        title="Charizard ex 199/165",
        price_usd=price,
        currency="USD",
        canonical_card_id=card.id,
        is_active=True,
    )
    sess.add(listing)
    sess.flush()
    return listing


def test_listing_below_threshold_creates_deal(session):
    settings = get_settings()
    settings.deal_margin_pct = 0.20
    settings.deal_min_benchmark_usd = 10
    card = _seed(session, market_price=100.0)
    listing = _make_listing(session, card, price=70.0)

    deal = evaluate_listing(session, listing)
    assert deal is not None
    assert deal.status == DealStatus.NEW
    assert deal.margin_pct == pytest.approx(0.30, rel=1e-3)
    assert deal.estimated_profit_usd > 0


def test_listing_at_market_does_not_create_deal(session):
    settings = get_settings()
    settings.deal_margin_pct = 0.20
    settings.deal_min_benchmark_usd = 10
    card = _seed(session, market_price=100.0)
    listing = _make_listing(session, card, price=95.0)

    deal = evaluate_listing(session, listing)
    assert deal is None


def test_low_value_card_filtered_by_floor(session):
    settings = get_settings()
    settings.deal_margin_pct = 0.20
    settings.deal_min_benchmark_usd = 10
    card = _seed(session, market_price=4.0)
    listing = _make_listing(session, card, price=1.0)

    deal = evaluate_listing(session, listing)
    assert deal is None


def test_recovered_listing_resets_expired_deal(session):
    settings = get_settings()
    settings.deal_margin_pct = 0.20
    settings.deal_min_benchmark_usd = 10
    card = _seed(session, market_price=100.0)
    listing = _make_listing(session, card, price=70.0)

    first = evaluate_listing(session, listing)
    assert first is not None

    # Price jumps above threshold — deal should expire.
    listing.price_usd = 95.0
    second = evaluate_listing(session, listing)
    assert second is None
    refreshed = session.get(type(first), first.id)
    assert refreshed.status == DealStatus.EXPIRED

    # Price drops back — deal should reactivate.
    listing.price_usd = 60.0
    third = evaluate_listing(session, listing)
    assert third is not None
    assert third.status == DealStatus.NEW
