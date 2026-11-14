"""Stop the daily analysis task started by its startup counterpart."""

import asyncio

import structlog
from fastapi import FastAPI

from api.lifespan.startup import daily_analysis as startup_side

logger = structlog.get_logger("api.crypto.daily")


async def shutdown(app: FastAPI) -> None:
    task = startup_side._task
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    startup_side._task = None
