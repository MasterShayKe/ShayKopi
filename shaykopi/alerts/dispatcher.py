"""Send deal alerts across configured channels with dedupe."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import AlertLog, Deal, DealStatus
from .discord import send_discord
from .telegram import send_telegram

log = logging.getLogger(__name__)


def _already_sent(sess: Session, listing_id: int, channel: str) -> bool:
    return sess.scalar(
        select(AlertLog).where(AlertLog.listing_id == listing_id, AlertLog.channel == channel)
    ) is not None


async def dispatch_deal(sess: Session, deal: Deal) -> None:
    """Fire alerts for `deal` on every configured channel that hasn't pinged it yet."""
    settings = get_settings()
    listing = deal.listing

    # Discord
    if settings.discord_webhook_url and not _already_sent(sess, listing.id, "discord"):
        ok, err = await send_discord(deal, listing)
        sess.add(AlertLog(listing_id=listing.id, channel="discord", ok=ok, error=err))

    # Telegram
    if settings.telegram_bot_token and settings.telegram_chat_id_list and not _already_sent(
        sess, listing.id, "telegram"
    ):
        ok, err = await send_telegram(deal, listing)
        sess.add(AlertLog(listing_id=listing.id, channel="telegram", ok=ok, error=err))

    if deal.status == DealStatus.NEW:
        deal.status = DealStatus.ALERTED


async def dispatch_new_deals(sess: Session) -> int:
    """Send pings for every NEW deal. Returns the number of deals processed."""
    deals = sess.scalars(select(Deal).where(Deal.status == DealStatus.NEW)).all()
    for d in deals:
        try:
            await dispatch_deal(sess, d)
        except Exception:  # never let one bad alert kill the loop
            log.exception("alert dispatch failed for deal %s", d.id)
    return len(deals)
