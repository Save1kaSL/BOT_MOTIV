from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from config import REQUIRED_CHANNEL, is_admin
from keyboards import CB_SUB_CHECK, subscription_gate_text, subscription_keyboard
from services.subscription import user_is_subscribed

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        if not REQUIRED_CHANNEL:
            return await handler(event, data)

        user_id: int | None = None
        bot = data.get("bot")

        if isinstance(event, CallbackQuery):
            if event.data == CB_SUB_CHECK:
                return await handler(event, data)
            user_id = event.from_user.id if event.from_user else None
            bot = bot or event.bot
        elif isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            bot = bot or event.bot

        if user_id is None or bot is None:
            return await handler(event, data)

        if is_admin(user_id) or await user_is_subscribed(bot, user_id):
            return await handler(event, data)

        text = subscription_gate_text()
        kb = subscription_keyboard()

        if isinstance(event, CallbackQuery):
            await event.answer("Сначала подпишись на канал", show_alert=True)
            if event.message:
                await event.message.answer(text, parse_mode="Markdown", reply_markup=kb)
        elif isinstance(event, Message):
            await event.answer(text, parse_mode="Markdown", reply_markup=kb)

        return None
