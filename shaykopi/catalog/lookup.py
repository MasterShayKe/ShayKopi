"""Resolve a ParsedTitle to a CanonicalCard row, if possible."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CanonicalCard
from .matcher import ParsedTitle


def resolve_canonical(sess: Session, parsed: ParsedTitle) -> CanonicalCard | None:
    """Try to find the canonical card for a parsed title.

    For One Piece we have set_code from the title.
    For Pokemon we typically only have number; we fall back to (game, number)
    which can be ambiguous across sets — the dashboard's /unmatched view is
    where humans correct that.
    """
    if parsed.game is None or parsed.number is None:
        return None

    stmt = select(CanonicalCard).where(
        CanonicalCard.game == parsed.game,
        CanonicalCard.number == parsed.number,
    )
    if parsed.set_code:
        stmt = stmt.where(CanonicalCard.set_code == parsed.set_code)

    rows = sess.scalars(stmt).all()
    if len(rows) == 1:
        return rows[0]
    # Ambiguous → don't guess; leave for manual triage.
    return None
