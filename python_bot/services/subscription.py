from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from config import REQUIRED_CHANNEL, is_admin

logger = logging.getLogger(__name__)

_SUBSCRIBED = frozenset(
    {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.RESTRICTED,
    }
)


async def user_is_subscribed(bot: Bot, user_id: int) -> bool:
    if is_admin(user_id):
        return True
    if not REQUIRED_CHANNEL:
        return True

    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in _SUBSCRIBED
    except TelegramBadRequest as e:
        logger.warning("Не удалось проверить подписку %s для %s: %s", REQUIRED_CHANNEL, user_id, e)
        return False
    except Exception:
        logger.exception("Ошибка проверки подписки для %s", user_id)
        return False
