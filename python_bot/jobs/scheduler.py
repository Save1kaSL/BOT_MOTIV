"""Фоновые задачи: reminders, retention."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from services.analytics import build_dashboard
from services.reminders import process_due_reminders
from services.retention import process_retention_due

logger = logging.getLogger(__name__)

INTERVAL_SEC = 300  # 5 min


async def background_loop(bot: Bot) -> None:
    logger.info("Background scheduler started (interval=%ss)", INTERVAL_SEC)
    while True:
        try:
            r = await process_due_reminders(bot)
            if r:
                logger.info("Sent %s reminders", r)
            rt = await process_retention_due(bot)
            if rt:
                logger.info("Processed %s retention notifications", rt)
            build_dashboard(refresh=True)
        except Exception:
            logger.exception("Background job error")
        await asyncio.sleep(INTERVAL_SEC)
