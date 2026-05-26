from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from handlers.start import send_welcome
from keyboards import CB_SUB_CHECK, subscription_gate_text, subscription_keyboard
from services.subscription import user_is_subscribed

router = Router()


@router.callback_query(F.data == CB_SUB_CHECK)
async def on_subscription_check(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.from_user or not callback.message:
        return

    if not await user_is_subscribed(callback.bot, callback.from_user.id):
        await callback.answer("Подпишись на канал и нажми снова", show_alert=True)
        await callback.message.answer(
            subscription_gate_text(),
            parse_mode="Markdown",
            reply_markup=subscription_keyboard(),
        )
        return

    await callback.answer("✅ Подписка подтверждена!")
    await send_welcome(callback.message, callback.from_user, state)
