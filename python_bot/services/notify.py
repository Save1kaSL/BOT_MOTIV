"""Уведомления админам."""

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import ADMIN_IDS
from keyboards import CB_ADM
from offers import get_offer


async def notify_admins_screenshots(bot: Bot, submission_id: int) -> None:
    from models.constants import TIMELINE_SCREENSHOT
    from services.timeline import log_timeline
    from storage import get_submission

    sub = get_submission(submission_id)
    if not sub:
        return

    log_timeline(
        sub["telegram_id"],
        TIMELINE_SCREENSHOT,
        offer_id=sub["offer_id"],
        title=f"Скрин {sub['submission_type']}",
        payload={"submission_id": submission_id},
    )

    offer = get_offer(sub["offer_id"])
    bank = offer.name if offer else sub["offer_id"]
    name = sub["first_name"] or sub["username"] or str(sub["telegram_id"])
    if sub["submission_type"] == "final":
        kind = "Финальное ЦД"
    elif sub["step_index"] is not None:
        kind = f"Шаг {sub['step_index'] + 1}"
    else:
        kind = "Скриншот"

    caption = (
        f"📸 *{kind}* — {bank}\n"
        f"👤 {name} (id `{sub['telegram_id']}`)\n"
        f"Заявка #{submission_id}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"{CB_ADM}subok:{submission_id}"),
                InlineKeyboardButton(text="✉️ Написать", callback_data=f"{CB_ADM}submsg:{submission_id}"),
            ],
        ]
    )

    for admin_id in ADMIN_IDS:
        try:
            for i, fid in enumerate(sub["file_ids"]):
                cap = caption if i == 0 else f"📎 Скрин {i + 1} — заявка #{submission_id}"
                await bot.send_photo(
                    admin_id,
                    fid,
                    caption=cap,
                    parse_mode="Markdown",
                    reply_markup=kb if i == 0 else None,
                )
        except Exception:
            pass
