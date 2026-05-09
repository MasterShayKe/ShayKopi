"""One Piece TCG catalog seeding via apitcg.com.

apitcg.com exposes a free One Piece endpoint:
    GET https://apitcg.com/api/one-piece/cards?set=OP-01

Returned shape (abridged):
    {"data": [{"id": "OP01-001", "code": "OP01-001", "name": "...",
               "set": {"name": "Romance Dawn", "code": "OP-01"},
               "images": {"small": "..."}, ...}]}
"""

from __future__ import annotations

import logging
import re

import httpx
from sqlalchemy import select

from ..config import get_settings
from ..db import session_scope
from ..models import CanonicalCard, Game

log = logging.getLogger(__name__)

API = "https://apitcg.com/api/one-piece/cards"

_NUMBER_FROM_CODE = re.compile(r"-(\d+)$")


async def fetch_set(set_code: str) -> list[dict]:
    settings = get_settings()
    headers = {"User-Agent": settings.user_agent}
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        r = await client.get(API, headers=headers, params={"set": set_code})
        r.raise_for_status()
        return (r.json() or {}).get("data", []) or []


async def seed_onepiece_set(set_code: str) -> int:
    cards = await fetch_set(set_code)
    inserted = 0
    with session_scope() as sess:
        for card in cards:
            code = card.get("code") or card.get("id") or ""
            m = _NUMBER_FROM_CODE.search(code)
            if not m:
                continue
            number = f"{int(m.group(1)):03d}"
            existing = sess.scalar(
                select(CanonicalCard).where(
                    CanonicalCard.game == Game.ONEPIECE,
                    CanonicalCard.set_code == set_code,
                    CanonicalCard.number == number,
                    CanonicalCard.variant == "normal",
                )
            )
            if existing is None:
                sess.add(
                    CanonicalCard(
                        game=Game.ONEPIECE,
                        set_code=set_code,
                        number=number,
                        name=card.get("name", ""),
                        variant="normal",
                        rarity=card.get("rarity"),
                        image_url=(card.get("images") or {}).get("small"),
                    )
                )
                inserted += 1

    log.info("Seeded One Piece set %s — %d new cards (payload: %d)", set_code, inserted, len(cards))
    return inserted
