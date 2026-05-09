"""Persist a stream of RawListing into the DB, matching to canonical cards."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..catalog.lookup import resolve_canonical
from ..catalog.matcher import parse_title
from ..models import Listing
from .base import RawListing

log = logging.getLogger(__name__)


def upsert_listing(sess: Session, raw: RawListing) -> Listing:
    """Insert or update by (site, external_id)."""
    existing = sess.scalar(
        select(Listing).where(Listing.site == raw.site, Listing.external_id == raw.external_id)
    )
    parsed = parse_title(raw.title)
    canonical = resolve_canonical(sess, parsed)
    grade = raw.grade or parsed.grade
    condition = raw.condition or parsed.condition

    now = datetime.now(UTC)
    if existing is None:
        listing = Listing(
            site=raw.site,
            external_id=raw.external_id,
            url=raw.url,
            title=raw.title,
            price_usd=raw.price_usd,
            currency=raw.currency,
            condition=condition,
            grade=grade,
            image_url=raw.image_url,
            canonical_card_id=canonical.id if canonical else None,
            is_active=True,
            raw=raw.raw,
            first_seen=now,
            last_seen=now,
        )
        sess.add(listing)
        sess.flush()
        return listing

    existing.price_usd = raw.price_usd
    existing.title = raw.title
    existing.url = raw.url
    existing.condition = condition
    existing.grade = grade
    existing.image_url = raw.image_url or existing.image_url
    if canonical and existing.canonical_card_id != canonical.id:
        existing.canonical_card_id = canonical.id
    existing.is_active = True
    existing.last_seen = now
    if raw.raw:
        existing.raw = raw.raw
    return existing
