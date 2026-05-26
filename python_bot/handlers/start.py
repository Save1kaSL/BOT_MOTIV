from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from formatters import format_onboarding_pick
from keyboards import ip_keyboard, reply_kb_for
from states import Onboarding
from config import is_admin
from storage import get_or_create_user

router = Router()


async def send_welcome(message: Message, user: User, state: FSMContext) -> None:
    await state.clear()
    db_user = get_or_create_user(user.id, user.username, user.first_name)
    from services.hooks import on_user_registered

    await on_user_registered(message.bot, user.id, user.username)
    name = user.first_name or "друг"

    if not db_user.onboarded:
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
    if is_admin(user.id):
        text += "\n🔐 *Админ* или /admin — панель управления."
    await message.answer(text, parse_mode="Markdown", reply_markup=reply_kb_for(user.id))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    u = message.from_user
    if not u:
        return
    await send_welcome(message, u, state)


@router.message(Onboarding.waiting_ip)
async def onboarding_ip_text(message: Message) -> None:
    await message.answer("Нажми кнопку: *Да, ИП есть* или *Нет ИП*", parse_mode="Markdown")
