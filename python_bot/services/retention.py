"""Retention tracking after approval."""

from __future__ import annotations

import logging

from config import ADMIN_IDS
from models.constants import PIPELINE_SAFE_PERIOD, RETENTION_PERIOD
from offers import get_offer
from repositories.offers_repo import get_user_offer_row, set_pipeline
from repositories.retention import list_due_retention_checks, mark_retention_notified, start_retention
from services.pipeline import advance_pipeline

logger = logging.getLogger(__name__)


def start_safe_period(telegram_id: int, offer_id: str) -> None:
    offer = get_offer(offer_id)
    row = get_user_offer_row(telegram_id, offer_id)
    if not offer or not row:
        return
    start_retention(row["id"], telegram_id, offer_id, offer.safe_period_days)
    advance_pipeline(telegram_id, offer_id, PIPELINE_SAFE_PERIOD, reason="safe_period_started")


async def process_retention_due(bot) -> int:
    count = 0
    for rt in list_due_retention_checks():
        uid = rt["telegram_id"]
        offer_id = rt["offer_id"]
        offer = get_offer(offer_id)
        bank = offer.name if offer else offer_id
        user_text = (
            f"✅ *{bank}* — защитный период завершён!\n"
            "Спасибо, что не закрывали счёт. Ожидайте основную выплату по графику."
        )
        admin_text = (
            f"📅 *Retention complete*\n{bank} | user `{uid}` | offer #{rt['user_offer_id']}"
        )
        if not rt["notified_user"]:
            try:
                await bot.send_message(uid, user_text, parse_mode="Markdown")
            except Exception as e:
                logger.warning("retention user %s: %s", uid, e)
        if not rt["notified_admin"]:
            for aid in ADMIN_IDS:
                try:
                    await bot.send_message(aid, admin_text, parse_mode="Markdown")
                except Exception:
                    pass
        mark_retention_notified(rt["id"], admin=True, user=True)
        row = get_user_offer_row(uid, offer_id)
        if row:
            set_pipeline(row["id"], "safe_complete", "одобрено")
        count += 1
    return count
