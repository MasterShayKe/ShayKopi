# ShayKopi

Card inventory & deal monitor for a Whatnot reselling partnership.

Scans **eBay**, **Hobbiesville**, **GameNerds**, and **TCGPlayer** every 15–30
minutes for **Pokémon TCG** and **One Piece TCG** singles, sealed product, and
graded slabs. Flags any listing that is meaningfully under-priced relative to:

- TCGPlayer market price
- eBay 30-day sold median
- Cross-site arbitrage (lowest current ask elsewhere)

Alerts go to **Discord**, **Telegram**, and a **FastAPI dashboard** for
triage.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env: at minimum set DISCORD_WEBHOOK_URL or TELEGRAM_BOT_TOKEN.

# 1. Seed catalog (Pokemon set + One Piece set)
shaykopi catalog seed --game pokemon --set sv3pt5
shaykopi catalog seed --game onepiece --set OP-01

# 2. One-shot scan (scrape -> match -> value -> store -> alert)
shaykopi scan --once

# 3. Dashboard
shaykopi web
# open http://127.0.0.1:8000/deals

# 4. Long-running scheduler (every SCAN_INTERVAL_MINUTES)
shaykopi schedule
```

## Architecture

See [`/root/.claude/plans/i-am-planning-to-linear-sparkle.md`](.) for the full
plan. Short version:

```
scrapers/  ->  catalog/matcher  ->  valuation/engine  ->  db
                                                          |
                                          alerts/{discord,telegram}
                                          web/ (dashboard)
```

- `shaykopi/scrapers/`  — one client per site, all yield `RawListing`
- `shaykopi/catalog/`   — Pokémon + One Piece card catalogs + title→canonical matcher
- `shaykopi/valuation/` — benchmarks (TCGPlayer / eBay sold / cross-site) and deal scoring
- `shaykopi/alerts/`    — Discord, Telegram, with `alert_log` dedupe
- `shaykopi/web/`       — FastAPI + Jinja2 + HTMX dashboard
- `shaykopi/scheduler.py` — APScheduler wiring

## Data sources

| Site         | Method                                                |
|--------------|-------------------------------------------------------|
| Hobbiesville | Shopify `/products.json` (no auth)                    |
| GameNerds    | Shopify `/products.json` (no auth)                    |
| TCGPlayer    | `pokemontcg.io` (Pokémon market) + `apitcg.com` (OP)  |
| eBay         | Browse API (active) + sold-listings page (comps)      |

## Testing

```bash
pytest
ruff check .
```

## Roadmap

1. **MVP**: Hobbiesville + Pokémon catalog + Discord alerts (this branch)
2. eBay + sold-comp benchmark
3. TCGPlayer market integration
4. GameNerds, full dashboard, Telegram
5. Dockerize, move to VPS
