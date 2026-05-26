from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from formatters import format_onboarding_pick
from keyboards import ip_keyboard, offers_list_keyboard, reply_kb_for
from keyboards import CB_PICK
from states import Onboarding
from config import is_admin
from storage import get_or_create_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    u = message.from_user
    if not u:
        return

    user = get_or_create_user(u.id, u.username, u.first_name)
    from services.hooks import on_user_registered

    await on_user_registered(message.bot, u.id, u.username)
    name = u.first_name or "друг"

    if not user.onboarded:
        await message.answer(
            f"👋 Привет, {name}!\n\n"
            "🤝 Партнёрка *РКО* — банковские офферы с выплатами.\n\n"
            "❓ *У тебя уже есть ИП?*",
            parse_mode="Markdown",
            reply_markup=ip_keyboard(),
        )
        await state.set_state(Onboarding.waiting_ip)
        return

    text = (
        f"👋 С возвращением, {name}!\n\n"
        "Кнопка *Офферы* или /offers — банки.\n"
        "👤 *Профиль* — холд и заявки."
    )
    if is_admin(u.id):
        text += "\n🔐 *Админ* или /admin — панель управления."
    await message.answer(text, parse_mode="Markdown", reply_markup=reply_kb_for(u.id))


@router.message(Onboarding.waiting_ip)
async def onboarding_ip_text(message: Message) -> None:
    await message.answer("Нажми кнопку: *Да, ИП есть* или *Нет ИП*", parse_mode="Markdown")
