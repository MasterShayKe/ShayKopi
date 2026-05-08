"""whatnot-prep — local Flask app that prices a card from a photo.

Pipeline per upload:
  1. Claude vision identifies the card and writes an eBay query.
  2. Scrape eBay sold listings for that query, summarise low/mid/high.
  3. Claude turns the metadata + comps into a tier, hype line, description
     and show-order score.
"""

from __future__ import annotations

import base64
import json
import os
import re
import statistics
from urllib.parse import quote_plus

import requests
from anthropic import Anthropic
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
PORT = int(os.environ.get("PORT", "5000"))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB upload cap
client = Anthropic()


# --- Prompts ----------------------------------------------------------------

VISION_SYSTEM = """You identify trading cards from photos for a Whatnot reseller.
Return ONLY a single JSON object, no prose, no markdown fences. Schema:
{
  "name": "card name",
  "set": "set name and year if visible, else null",
  "number": "card number e.g. 25/102, else null",
  "rarity": "Common/Uncommon/Rare/Holo/Ultra Rare/Secret Rare/etc, else null",
  "variant": "1st Edition / Reverse Holo / Shadowless / Foil / Promo / none",
  "condition": "Mint / Near Mint / Lightly Played / Played / Damaged",
  "ebay_query": "optimised eBay search string for finding SOLD comparable copies. Include set, name, number and variant. Do not include condition. Keep it under 12 words."
}
If something is not visible, use null. Do not guess wildly."""

TIER_SYSTEM = """You are an expert Whatnot live-show host pricing trading cards.
Given card metadata + recent sold prices, return ONLY a single JSON object:
{
  "tier": "HEAT" | "SOLID" | "FILLER",
  "hype_line": "one punchy auctioneer line, max 18 words, no emojis",
  "whatnot_description": "2-3 plain-text sentences for the listing description",
  "show_order_score": 0-100 integer (filler low, heat high; biggest hits close the show)
}
Tiering rules:
- HEAT  = mid sold price >= $40, OR rare/secret/ultra rare, OR a notable variant (1st edition, shadowless, alt art).
- SOLID = mid sold price between $10 and $40.
- FILLER = mid sold price below $10, or no comps and unremarkable card.
If price data is missing, use the rarity/variant signal to choose a tier and pick a conservative score.
Return ONLY the JSON object, no prose."""


# --- Claude calls -----------------------------------------------------------

def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Pull the first {...} block to be defensive against stray prose.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def analyze_image(image_bytes: bytes, media_type: str) -> dict:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=600,
        system=[{"type": "text", "text": VISION_SYSTEM,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": "Identify this card and produce the JSON."},
            ],
        }],
    )
    return _parse_json(msg.content[0].text)


def tier_card(card: dict, prices: dict) -> dict:
    payload = json.dumps({"card": card, "prices": prices}, ensure_ascii=False)
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=600,
        system=[{"type": "text", "text": TIER_SYSTEM,
                 "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": payload}],
    )
    return _parse_json(msg.content[0].text)


# --- eBay scraping ----------------------------------------------------------

EBAY_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

PRICE_RE = re.compile(r"\$?([\d,]+(?:\.\d{1,2})?)")


def scrape_sold_prices(query: str, limit: int = 10) -> list[float]:
    if not query:
        return []
    url = (
        "https://www.ebay.com/sch/i.html"
        f"?_nkw={quote_plus(query)}"
        "&LH_Sold=1&LH_Complete=1"
        "&_ipg=60&_sop=13"  # _sop=13 = recently ended
    )
    resp = requests.get(url, headers=EBAY_HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    prices: list[float] = []
    for item in soup.select("li.s-item"):
        title_el = item.select_one(".s-item__title")
        if title_el and "Shop on eBay" in title_el.get_text():
            continue
        price_el = item.select_one(".s-item__price")
        if not price_el:
            continue
        text = price_el.get_text(" ", strip=True)
        match = PRICE_RE.search(text)
        if not match:
            continue
        try:
            value = float(match.group(1).replace(",", ""))
        except ValueError:
            continue
        if value <= 0:
            continue
        prices.append(value)
        if len(prices) >= limit:
            break
    return prices


def summarise_prices(prices: list[float]) -> dict:
    if not prices:
        return {"low": None, "mid": None, "high": None, "count": 0, "samples": []}
    return {
        "low": round(min(prices), 2),
        "mid": round(statistics.median(prices), 2),
        "high": round(max(prices), 2),
        "count": len(prices),
        "samples": [round(p, 2) for p in prices],
    }


# --- Routes -----------------------------------------------------------------

ALLOWED_MEDIA = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    f = request.files["image"]
    image_bytes = f.read()
    if not image_bytes:
        return jsonify({"error": "Empty image"}), 400

    media_type = (f.mimetype or "image/jpeg").lower()
    if media_type not in ALLOWED_MEDIA:
        media_type = "image/jpeg"

    try:
        card = analyze_image(image_bytes, media_type)
    except Exception as exc:  # noqa: BLE001 — surface error to the UI
        return jsonify({"error": f"Vision step failed: {exc}"}), 502

    query = (card.get("ebay_query") or card.get("name") or "").strip()
    scrape_error: str | None = None
    try:
        raw = scrape_sold_prices(query)
    except Exception as exc:  # noqa: BLE001
        raw = []
        scrape_error = str(exc)
    prices = summarise_prices(raw)

    try:
        tier = tier_card(card, prices)
    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "error": f"Tier step failed: {exc}",
            "card": card,
            "prices": prices,
        }), 502

    return jsonify({
        "card": card,
        "prices": prices,
        "tier": tier,
        "ebay_query": query,
        "scrape_error": scrape_error,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
