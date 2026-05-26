"""Реквизиты для выплат."""

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from states import PayoutDetails
from storage import get_or_create_user, save_payment_details

router = Router()


@router.message(PayoutDetails.waiting_requisites)
async def on_payment_details(message: Message, state: FSMContext) -> None:
    if not message.from_user or not message.text:
        await message.answer("Пришлите реквизиты текстом одним сообщением.")
        return

    uid = message.from_user.id
    save_payment_details(uid, message.text)
    await state.clear()

    user = get_or_create_user(uid, message.from_user.username, message.from_user.first_name)
    name = user.first_name or user.username or str(uid)

    admin_text = (
        f"📋 *Реквизиты от пользователя*\n"
        f"👤 {name} (id `{uid}`)\n\n"
        f"{message.text}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, admin_text, parse_mode="Markdown")
        except Exception:
            pass

    await message.answer(
        "✅ Реквизиты сохранены и переданы админу.\n"
        "По авансу — ожидайте связи или напишите сюда, если админ ещё не ответил.",
        parse_mode="Markdown",
    )
