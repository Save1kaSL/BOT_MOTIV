from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.offers import show_offers_list
from keyboards import reply_kb_for

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    await message.answer(
        "🏠 *Меню*\n\n"
        "• *Офферы* или /offers — банки\n"
        "• *Профиль* — холд и заявки\n"
        "• /start — сначала",
        parse_mode="Markdown",
        reply_markup=reply_kb_for(uid),
    )
    await show_offers_list(message)
