"""Pokémon TCG catalog seeding via pokemontcg.io.

Free public API, no auth required for low-volume use. With a free API key
the rate limit jumps from 1000/day to 20000/day.

We pull cards by set ID (e.g. ``sv3pt5`` for "151") and persist them as
CanonicalCard rows. The same call returns ``tcgplayer.prices`` which we
cache as a TCGPLAYER_MARKET benchmark.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select

from ..config import get_settings
from ..db import session_scope
from ..models import Benchmark, BenchmarkType, CanonicalCard, Game

log = logging.getLogger(__name__)

API = "https://api.pokemontcg.io/v2/cards"


async def fetch_set(set_id: str, *, page_size: int = 250) -> list[dict]:
    """Return all cards in a Pokemon set."""
    settings = get_settings()
    headers = {"User-Agent": settings.user_agent}
    if settings.pokemontcg_api_key:
        headers["X-Api-Key"] = settings.pokemontcg_api_key

    cards: list[dict] = []
    page = 1
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        while True:
            r = await client.get(
                API,
                headers=headers,
                params={"q": f"set.id:{set_id}", "page": page, "pageSize": page_size},
            )
            r.raise_for_status()
            payload = r.json()
            data = payload.get("data", [])
            cards.extend(data)
            if len(data) < page_size:
                break
            page += 1
    return cards


def _market_price(card: dict) -> float | None:
    """Pull the most representative TCGPlayer market price from the card payload."""
    prices = (card.get("tcgplayer") or {}).get("prices") or {}
    # Prefer holofoil/normal/reverseHolofoil in that order
    for key in ("holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil", "unlimitedHolofoil"):
        bucket = prices.get(key)
        if bucket and bucket.get("market"):
            return float(bucket["market"])
    # Fall back to the first bucket with a market price
    for bucket in prices.values():
        if isinstance(bucket, dict) and bucket.get("market"):
            return float(bucket["market"])
    return None


async def seed_pokemon_set(set_id: str) -> int:
    cards = await fetch_set(set_id)
    inserted = 0
    now = datetime.now(UTC)
    with session_scope() as sess:
        for card in cards:
            number = card.get("number")
            if not number:
                continue
            existing = sess.scalar(
                select(CanonicalCard).where(
                    CanonicalCard.game == Game.POKEMON,
                    CanonicalCard.set_code == set_id,
                    CanonicalCard.number == number,
                    CanonicalCard.variant == "normal",
                )
            )
            if existing is None:
                existing = CanonicalCard(
                    game=Game.POKEMON,
                    set_code=set_id,
                    number=number,
                    name=card.get("name", ""),
                    variant="normal",
                    rarity=card.get("rarity"),
                    image_url=(card.get("images") or {}).get("small"),
                )
                sess.add(existing)
                sess.flush()
                inserted += 1

            market = _market_price(card)
            if market is not None:
                bench = sess.scalar(
                    select(Benchmark).where(
                        Benchmark.canonical_card_id == existing.id,
                        Benchmark.benchmark_type == BenchmarkType.TCGPLAYER_MARKET,
                    )
                )
                if bench is None:
                    sess.add(
                        Benchmark(
                            canonical_card_id=existing.id,
                            benchmark_type=BenchmarkType.TCGPLAYER_MARKET,
                            value_usd=market,
                            sample_size=1,
                            as_of=now,
                        )
                    )
                else:
                    bench.value_usd = market
                    bench.as_of = now

    log.info("Seeded Pokemon set %s — %d new cards (total payload: %d)", set_id, inserted, len(cards))
    return inserted
