"""Telegram bot alerter."""

from __future__ import annotations

import logging

import httpx

from ..config import get_settings
from ..models import Deal, Listing

log = logging.getLogger(__name__)


async def send_telegram(deal: Deal, listing: Listing) -> tuple[bool, str | None]:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id_list:
        return False, "no telegram configured"

    margin = deal.margin_pct or 0
    text = (
        f"<b>Deal — {margin * 100:.0f}% under benchmark</b>\n"
        f"<a href=\"{listing.url}\">{listing.title}</a>\n"
        f"Site: {listing.site.value}\n"
        f"Price: ${listing.price_usd:.2f}  •  "
        f"Bench: ${deal.benchmark_value_usd:.2f} ({deal.benchmark_type.value})\n"
        f"Est. profit: ${deal.estimated_profit_usd:.2f}"
    )

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    last_err: str | None = None
    sent_any = False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            for chat_id in settings.telegram_chat_id_list:
                try:
                    r = await client.post(
                        url,
                        json={
                            "chat_id": chat_id,
                            "text": text,
                            "parse_mode": "HTML",
                            "disable_web_page_preview": False,
                        },
                    )
                    r.raise_for_status()
                    sent_any = True
                except Exception as e:
                    last_err = str(e)[:480]
                    log.warning("telegram chat %s failed: %s", chat_id, e)
    except Exception as e:
        return False, str(e)[:480]
    return sent_any, last_err
