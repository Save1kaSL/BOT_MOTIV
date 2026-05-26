"""Запрос выполнения ЦД — уведомление админу."""

from __future__ import annotations

import logging

from aiogram import Bot
from config import ADMIN_IDS
from offers import get_offer
from storage import get_contact_username, get_or_create_user

logger = logging.getLogger(__name__)


async def notify_cd_request(
    bot: Bot,
    telegram_id: int,
    offer_id: str,
    *,
    first_name: str | None = None,
    tg_username: str | None = None,
) -> None:
    offer = get_offer(offer_id)
    bank = offer.name if offer else offer_id
    contact = get_contact_username(telegram_id)
    uname = f"@{contact}" if contact else "— не указан"

    text = (
        f"📣 *Запрос на выполнение ЦД*\n\n"
        f"🏦 *{bank}*\n"
        f"👤 {first_name or '—'} | Telegram: `{telegram_id}`\n"
        f"📎 Username для связи: {uname}\n\n"
        "_Свяжись с пользователем и помоги завершить целевое действие._"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown")
        except Exception as e:
            logger.warning("cd_request notify %s: %s", admin_id, e)
