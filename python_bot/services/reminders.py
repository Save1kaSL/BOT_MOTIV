"""Auto reminder system."""

from __future__ import annotations

import logging

from models.constants import (
    REMINDER_DONT_CLOSE,
    REMINDER_INTERVALS_HOURS,
    REMINDER_SAFE_ACTIVE,
    REMINDER_SAFE_DAYS,
    REMINDER_SCREENSHOT,
    REMINDER_STEP,
    REMINDER_QUICK_30M,
    REMINDER_QUICK_8H,
)
from offers import get_offer
from repositories.reminders import list_due_reminders, mark_sent, schedule_reminder
from repositories.offers_repo import get_user_offer_row

logger = logging.getLogger(__name__)

REMINDER_TEXTS = {
    REMINDER_STEP: "🔔 Напоминание: выполни следующий шаг по офферу *{bank}*.",
    REMINDER_SCREENSHOT: "📸 Напоминание: загрузи скриншот подтверждения для *{bank}*.",
    REMINDER_SAFE_DAYS: "⏳ До конца защитного периода *{bank}*: ~{days} дн. Не закрывай счёт!",
    REMINDER_DONT_CLOSE: "⚠️ *{bank}*: не закрывай счёт до окончания защитного периода!",
    REMINDER_SAFE_ACTIVE: "🛡 Защитный период по *{bank}* активен. Соблюдай условия банка.",
    REMINDER_QUICK_30M: "⏱ *{bank}*: прошло 30 минут — можешь вернуться и продолжить шаги в боте.",
    REMINDER_QUICK_8H: "🔔 *{bank}*: прошло 8 часов. Возвращайся в бота — офферы ждут тебя.",
}

def schedule_quick_reminders(telegram_id: int, offer_id: str) -> None:
    # 30 минут и 8 часов
    schedule_reminder(telegram_id, REMINDER_QUICK_30M, 1, offer_id=offer_id, payload={"minutes": 30})
    schedule_reminder(telegram_id, REMINDER_QUICK_8H, 8, offer_id=offer_id, payload={"hours": 8})


def schedule_offer_reminders(telegram_id: int, offer_id: str) -> None:
    offer = get_offer(offer_id)
    if not offer:
        return
    for hours in REMINDER_INTERVALS_HOURS:
        schedule_reminder(telegram_id, REMINDER_STEP, hours, offer_id=offer_id)
        schedule_reminder(telegram_id, REMINDER_SCREENSHOT, hours + 2, offer_id=offer_id)
    schedule_quick_reminders(telegram_id, offer_id)
    schedule_reminder(
        telegram_id, REMINDER_SAFE_ACTIVE, 24, offer_id=offer_id,
        payload={"days": offer.safe_period_days},
    )
    schedule_reminder(
        telegram_id, REMINDER_DONT_CLOSE, 72, offer_id=offer_id,
    )


def schedule_safe_period_reminders(telegram_id: int, offer_id: str, days_left: int) -> None:
    for hours in REMINDER_INTERVALS_HOURS:
        schedule_reminder(
            telegram_id, REMINDER_SAFE_DAYS, hours,
            offer_id=offer_id, payload={"days": days_left},
        )


async def process_due_reminders(bot) -> int:
    sent = 0
    for r in list_due_reminders():
        uid = r["telegram_id"]
        offer_id = r.get("offer_id")
        offer = get_offer(offer_id) if offer_id else None
        bank = offer.name if offer else "офферу"
        tpl = REMINDER_TEXTS.get(r["reminder_type"], "🔔 Напоминание по {bank}")
        import json
        payload = json.loads(r.get("payload") or "{}")
        text = tpl.format(bank=bank, days=payload.get("days", "?"))
        try:
            await bot.send_message(uid, text, parse_mode="Markdown")
            mark_sent(r["id"])
            sent += 1
        except Exception as e:
            logger.warning("reminder %s -> %s: %s", r["id"], uid, e)
    return sent
