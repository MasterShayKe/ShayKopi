"""SQLAlchemy ORM models."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Game(enum.StrEnum):
    POKEMON = "pokemon"
    ONEPIECE = "onepiece"


class Site(enum.StrEnum):
    EBAY = "ebay"
    TCGPLAYER = "tcgplayer"
    HOBBIESVILLE = "hobbiesville"
    GAMENERDS = "gamenerds"


class BenchmarkType(enum.StrEnum):
    TCGPLAYER_MARKET = "tcgplayer_market"
    EBAY_SOLD_MEDIAN = "ebay_sold_median"
    CROSS_SITE_MIN = "cross_site_min"


class DealStatus(enum.StrEnum):
    NEW = "new"
    ALERTED = "alerted"
    BOUGHT = "bought"
    IGNORED = "ignored"
    EXPIRED = "expired"


class CanonicalCard(Base):
    __tablename__ = "canonical_cards"
    __table_args__ = (
        UniqueConstraint("game", "set_code", "number", "variant", name="uq_canonical"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game: Mapped[Game] = mapped_column(Enum(Game), index=True)
    set_code: Mapped[str] = mapped_column(String(32), index=True)
    number: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(256), index=True)
    variant: Mapped[str] = mapped_column(String(64), default="normal")
    rarity: Mapped[str | None] = mapped_column(String(64))
    image_url: Mapped[str | None] = mapped_column(String(512))

    listings: Mapped[list[Listing]] = relationship(back_populates="canonical")


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listing_site_extid", "site", "external_id", unique=True),
        Index("ix_listing_active_canonical", "is_active", "canonical_card_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site: Mapped[Site] = mapped_column(Enum(Site), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(512))
    price_usd: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    condition: Mapped[str | None] = mapped_column(String(64))
    grade: Mapped[str | None] = mapped_column(String(32))
    image_url: Mapped[str | None] = mapped_column(String(512))

    canonical_card_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_cards.id"), index=True
    )
    canonical: Mapped[CanonicalCard | None] = relationship(back_populates="listings")

    first_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    raw: Mapped[dict | None] = mapped_column(JSON)


class SoldComp(Base):
    """eBay (or other) recently-sold rows used to compute median benchmarks."""

    __tablename__ = "sold_comps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_card_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_cards.id"), index=True
    )
    site: Mapped[Site] = mapped_column(Enum(Site))
    sold_price_usd: Mapped[float] = mapped_column(Float)
    sold_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    title: Mapped[str] = mapped_column(String(512))
    grade: Mapped[str | None] = mapped_column(String(32))


class Benchmark(Base):
    __tablename__ = "benchmarks"
    __table_args__ = (
        UniqueConstraint("canonical_card_id", "benchmark_type", name="uq_bench"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_card_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_cards.id"), index=True
    )
    benchmark_type: Mapped[BenchmarkType] = mapped_column(Enum(BenchmarkType))
    value_usd: Mapped[float] = mapped_column(Float)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    as_of: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), unique=True)
    benchmark_type: Mapped[BenchmarkType] = mapped_column(Enum(BenchmarkType))
    benchmark_value_usd: Mapped[float] = mapped_column(Float)
    margin_pct: Mapped[float] = mapped_column(Float)
    estimated_profit_usd: Mapped[float] = mapped_column(Float)
    status: Mapped[DealStatus] = mapped_column(
        Enum(DealStatus), default=DealStatus.NEW, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(String(1024))

    listing: Mapped[Listing] = relationship()


class AlertLog(Base):
    __tablename__ = "alert_log"
    __table_args__ = (
        UniqueConstraint("listing_id", "channel", name="uq_alert"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32))
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ok: Mapped[bool] = mapped_column(default=True)
    error: Mapped[str | None] = mapped_column(String(512))
