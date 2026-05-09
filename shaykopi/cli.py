"""Command-line entrypoint: ``shaykopi <command>``."""

from __future__ import annotations

import asyncio
import logging

import typer
import uvicorn
from rich import print as rprint
from rich.table import Table

from .catalog.onepiece import seed_onepiece_set
from .catalog.pokemon import seed_pokemon_set
from .config import get_settings
from .db import init_db
from .models import Game
from .scan import run_scan
from .scheduler import main as scheduler_main

app = typer.Typer(no_args_is_help=True)
catalog_app = typer.Typer(help="Seed canonical card catalogs.")
app.add_typer(catalog_app, name="catalog")


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@app.command()
def init(verbose: bool = False) -> None:
    """Create DB tables (no-op if they already exist)."""
    _setup_logging(verbose)
    init_db()
    rprint("[green]ok[/green] database initialised")


@catalog_app.command("seed")
def catalog_seed(
    game: Game = typer.Option(..., help="Card game"),
    set_id: str = typer.Option(..., "--set", help="Set ID — e.g. sv3pt5 (Pokemon) or OP-01 (One Piece)"),
    verbose: bool = False,
) -> None:
    _setup_logging(verbose)
    init_db()
    if game == Game.POKEMON:
        n = asyncio.run(seed_pokemon_set(set_id))
    else:
        n = asyncio.run(seed_onepiece_set(set_id))
    rprint(f"[green]seeded[/green] {n} new cards into {game.value}/{set_id}")


@app.command()
def scan(
    once: bool = typer.Option(True, help="Run a single scan and exit"),
    limit: int = typer.Option(None, help="Cap listings per source (debug)"),
    verbose: bool = False,
) -> None:
    """Run a scan cycle: scrape -> match -> value -> alert."""
    _setup_logging(verbose)
    init_db()
    summary = asyncio.run(run_scan(limit=limit))
    table = Table("source", "result")
    for k, v in summary.items():
        table.add_row(k, str(v))
    rprint(table)
    if not once:
        scheduler_main()


@app.command()
def schedule(verbose: bool = False) -> None:
    """Long-running scheduler — scans every SCAN_INTERVAL_MINUTES."""
    _setup_logging(verbose)
    scheduler_main()


@app.command()
def web(
    host: str = typer.Option(None, help="Bind host (defaults to WEB_HOST)"),
    port: int = typer.Option(None, help="Bind port (defaults to WEB_PORT)"),
) -> None:
    """Run the FastAPI dashboard."""
    settings = get_settings()
    uvicorn.run(
        "shaykopi.web.app:app",
        host=host or settings.web_host,
        port=port or settings.web_port,
        reload=False,
    )


if __name__ == "__main__":
    app()
