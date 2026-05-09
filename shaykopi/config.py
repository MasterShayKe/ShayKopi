"""Runtime configuration loaded from environment / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./shaykopi.db"

    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    http_timeout_seconds: float = 30.0
    scan_interval_minutes: int = 20

    deal_margin_pct: float = 0.20
    deal_min_benchmark_usd: float = 10.0
    whatnot_fee_pct: float = 0.08
    shipping_cost_usd: float = 1.50

    pokemontcg_api_key: str | None = None
    ebay_app_id: str | None = None
    ebay_marketplace: str = "EBAY_US"

    discord_webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_ids: str = ""

    web_host: str = "127.0.0.1"
    web_port: int = 8000

    @property
    def telegram_chat_id_list(self) -> list[str]:
        return [c.strip() for c in self.telegram_chat_ids.split(",") if c.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
