"""Start the daily analysis task: one stored snapshot per UTC day at the configured hour.

The hour is ``CRYPTO_DAILY_HOUR_UTC`` (default 6). The task also backfills a missing
snapshot right at startup, so a redeploy never leaves the day without an analysis.
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import FastAPI

from api.routers.api.crypto.route import _build_analysis, _store_snapshot
from api.services.crypto_analysis import utc_today

logger = structlog.get_logger("api.crypto.daily")

_task: asyncio.Task[None] | None = None


def _daily_hour_utc() -> int:
    try:
        return max(0, min(23, int(os.environ.get("CRYPTO_DAILY_HOUR_UTC", "6"))))
    except ValueError:
        return 6


def _seconds_until_next_run(now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    target = now.replace(hour=_daily_hour_utc(), minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def _run_daily() -> None:
    while True:
        await asyncio.sleep(_seconds_until_next_run())
        try:
            payload = await _build_analysis()
            await _store_snapshot(payload)
            logger.info("daily_analysis_stored", date_key=utc_today())
        except Exception:  # noqa: BLE001 - one failed run must not kill the loop
            logger.exception("daily_analysis_failed")


async def startup(app: FastAPI) -> None:
    global _task

    async def backfill() -> None:
        try:
            payload = await _build_analysis()
            await _store_snapshot(payload)
            logger.info("startup_analysis_stored", date_key=utc_today())
        except Exception:  # noqa: BLE001
            logger.exception("startup_analysis_failed")

    _task = asyncio.create_task(_run_daily())
    asyncio.create_task(backfill())
