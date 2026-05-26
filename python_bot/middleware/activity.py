"""Трекинг активности для scoring."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from services.lead_scoring import record_user_activity

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class ActivityMiddleware(BaseMiddleware):
    async def __call__(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        if isinstance(event, Message) and event.from_user:
            record_user_activity(event.from_user.id)
        return await handler(event, data)
