"""Long-running APScheduler that fires a scan every SCAN_INTERVAL_MINUTES."""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import get_settings
from .db import init_db
from .scan import run_scan

log = logging.getLogger(__name__)


async def _run_scheduler() -> None:
    init_db()
    settings = get_settings()
    sched = AsyncIOScheduler()
    sched.add_job(
        run_scan,
        "interval",
        minutes=settings.scan_interval_minutes,
        next_run_time=None,
        id="scan",
        max_instances=1,
        coalesce=True,
    )
    sched.start()
    log.info("scheduler running every %d minutes", settings.scan_interval_minutes)
    # Kick off an immediate scan, then idle.
    await run_scan()
    while True:
        await asyncio.sleep(3600)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(_run_scheduler())


if __name__ == "__main__":
    main()
