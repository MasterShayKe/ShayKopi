"""FastAPI + Jinja2 + HTMX dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select

from ..db import init_db, session_scope
from ..models import Deal, DealStatus, Listing, Site

BASE = Path(__file__).parent
TEMPLATES = Jinja2Templates(directory=str(BASE / "templates"))

app = FastAPI(title="ShayKopi")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/", response_class=RedirectResponse)
def root() -> RedirectResponse:
    return RedirectResponse("/deals")


@app.get("/deals", response_class=HTMLResponse)
def deals_index(
    request: Request,
    site: str | None = None,
    status: str = "new,alerted",
    min_profit: float = 0.0,
):
    statuses = [DealStatus(s.strip()) for s in status.split(",") if s.strip()]
    with session_scope() as sess:
        stmt = (
            select(Deal)
            .join(Listing, Deal.listing_id == Listing.id)
            .where(Deal.status.in_(statuses))
            .where(Deal.estimated_profit_usd >= min_profit)
            .order_by(desc(Deal.margin_pct))
            .limit(500)
        )
        if site:
            stmt = stmt.where(Listing.site == Site(site))
        deals = sess.scalars(stmt).all()
        rows = [
            {
                "id": d.id,
                "site": d.listing.site.value,
                "title": d.listing.title,
                "url": d.listing.url,
                "image": d.listing.image_url,
                "price": d.listing.price_usd,
                "benchmark": d.benchmark_value_usd,
                "benchmark_type": d.benchmark_type.value,
                "margin": d.margin_pct,
                "profit": d.estimated_profit_usd,
                "status": d.status.value,
                "card_name": d.listing.canonical.name if d.listing.canonical else None,
            }
            for d in deals
        ]
    return TEMPLATES.TemplateResponse(
        "deals.html",
        {
            "request": request,
            "deals": rows,
            "filter_site": site or "",
            "filter_status": status,
            "filter_min_profit": min_profit,
            "sites": [s.value for s in Site],
        },
    )


@app.post("/deals/{deal_id}/status")
def set_deal_status(deal_id: int, status: str = Form(...)):
    new_status = DealStatus(status)
    with session_scope() as sess:
        deal = sess.get(Deal, deal_id)
        if deal is None:
            raise HTTPException(404)
        deal.status = new_status
    return RedirectResponse("/deals", status_code=303)


@app.get("/unmatched", response_class=HTMLResponse)
def unmatched(request: Request):
    with session_scope() as sess:
        listings = sess.scalars(
            select(Listing)
            .where(Listing.is_active == True, Listing.canonical_card_id.is_(None))  # noqa: E712
            .order_by(desc(Listing.last_seen))
            .limit(200)
        ).all()
        rows = [
            {
                "id": x.id,
                "site": x.site.value,
                "title": x.title,
                "url": x.url,
                "price": x.price_usd,
                "image": x.image_url,
            }
            for x in listings
        ]
    return TEMPLATES.TemplateResponse(
        "unmatched.html", {"request": request, "listings": rows}
    )
