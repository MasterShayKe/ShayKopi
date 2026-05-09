"""Discord webhook alerter."""

from __future__ import annotations

import logging

import httpx

from ..config import get_settings
from ..models import Deal, Listing

log = logging.getLogger(__name__)


def _color_for_margin(margin_pct: float) -> int:
    if margin_pct >= 0.50:
        return 0xE91E63  # pink — fire deal
    if margin_pct >= 0.30:
        return 0xFF9800  # orange
    return 0x4CAF50  # green


async def send_discord(deal: Deal, listing: Listing) -> tuple[bool, str | None]:
    settings = get_settings()
    if not settings.discord_webhook_url:
        return False, "no webhook configured"

    margin = deal.margin_pct or 0
    embed = {
        "title": listing.title[:240],
        "url": listing.url,
        "color": _color_for_margin(margin),
        "fields": [
            {"name": "Site", "value": listing.site.value, "inline": True},
            {"name": "Price", "value": f"${listing.price_usd:.2f}", "inline": True},
            {"name": "Benchmark", "value": f"${deal.benchmark_value_usd:.2f} ({deal.benchmark_type.value})", "inline": True},
            {"name": "Margin", "value": f"{margin * 100:.0f}%", "inline": True},
            {"name": "Est. profit", "value": f"${deal.estimated_profit_usd:.2f}", "inline": True},
        ],
    }
    if listing.image_url:
        embed["thumbnail"] = {"url": listing.image_url}

    payload = {
        "username": "ShayKopi",
        "content": f"Deal: **{margin * 100:.0f}% under** benchmark — ${deal.estimated_profit_usd:.2f} est. profit",
        "embeds": [embed],
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(settings.discord_webhook_url, json=payload)
            r.raise_for_status()
        return True, None
    except Exception as e:
        log.warning("discord post failed: %s", e)
        return False, str(e)[:480]
