from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.google_sheets_archive_export import build_year_export_payloads, post_payload_sequence

logger = logging.getLogger("contrast.performance")
ARCHIVE_TZ = ZoneInfo("Asia/Qyzylorda")
_daily_export_task: asyncio.Task | None = None


def seconds_until_next_daily_run(now: datetime | None = None) -> float:
    settings = get_settings()
    current = now or datetime.now(ARCHIVE_TZ)
    target = current.replace(
        hour=max(0, min(23, settings.GOOGLE_SHEETS_DAILY_EXPORT_HOUR)),
        minute=max(0, min(59, settings.GOOGLE_SHEETS_DAILY_EXPORT_MINUTE)),
        second=0,
        microsecond=0,
    )
    if target <= current:
        target += timedelta(days=1)
    return max(1.0, (target - current).total_seconds())


def run_daily_google_sheets_export_once() -> dict:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured")

    current_year = datetime.now(ARCHIVE_TZ).year
    db = SessionLocal()
    try:
        payloads = build_year_export_payloads(db, current_year, None)
        return post_payload_sequence(payloads)
    finally:
        db.close()


async def _daily_google_sheets_export_loop() -> None:
    settings = get_settings()
    logger.info(
        "google-sheets-daily-export scheduler started at %02d:%02d Asia/Qyzylorda",
        settings.GOOGLE_SHEETS_DAILY_EXPORT_HOUR,
        settings.GOOGLE_SHEETS_DAILY_EXPORT_MINUTE,
    )
    while True:
        await asyncio.sleep(seconds_until_next_daily_run())
        try:
            result = await asyncio.to_thread(run_daily_google_sheets_export_once)
            logger.info("google-sheets-daily-export completed ok=%s sheets=%s", result.get("ok"), result.get("updated_sheets"))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("google-sheets-daily-export failed: %s", exc)


def start_daily_google_sheets_export_scheduler() -> None:
    global _daily_export_task
    settings = get_settings()
    if not settings.GOOGLE_SHEETS_DAILY_EXPORT_ENABLED:
        logger.info("google-sheets-daily-export scheduler disabled by GOOGLE_SHEETS_DAILY_EXPORT_ENABLED")
        return
    if not settings.GOOGLE_SHEETS_EXPORT_WEBHOOK_URL:
        logger.info("google-sheets-daily-export scheduler skipped: GOOGLE_SHEETS_EXPORT_WEBHOOK_URL is not configured")
        return
    if SessionLocal is None:
        logger.info("google-sheets-daily-export scheduler skipped: DATABASE_URL is not configured")
        return
    if _daily_export_task and not _daily_export_task.done():
        return
    _daily_export_task = asyncio.create_task(_daily_google_sheets_export_loop())


async def stop_daily_google_sheets_export_scheduler() -> None:
    global _daily_export_task
    if not _daily_export_task:
        return
    _daily_export_task.cancel()
    try:
        await _daily_export_task
    except asyncio.CancelledError:
        pass
    _daily_export_task = None
