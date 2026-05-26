import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

import os

from config import BOT_TOKEN, REQUIRED_CHANNEL, TELEGRAM_PROXY
from handlers import setup_routers
from jobs.scheduler import background_loop
from keyboards import BOT_COMMANDS
from middleware.activity import ActivityMiddleware
from middleware.subscription import SubscriptionMiddleware
from storage import init_db

_log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(
    level=_log_level,
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Долгий таймаут — у многих Telegram API отвечает медленно / нужен VPN
SESSION_TIMEOUT = 120


async def setup_commands(bot: Bot) -> None:
    for attempt in range(1, 4):
        try:
            await bot.set_my_commands(BOT_COMMANDS, request_timeout=SESSION_TIMEOUT)
            logger.info("Меню команд Telegram установлено")
            return
        except TelegramNetworkError as e:
            logger.warning("set_my_commands попытка %s/3: %s", attempt, e)
            await asyncio.sleep(3)
    logger.warning("Меню /offers /admin не зарегистрировано в API — кнопки внизу работают")


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан в .env")
        sys.exit(1)

    init_db()

    session = AiohttpSession(timeout=SESSION_TIMEOUT, proxy=TELEGRAM_PROXY)
    if TELEGRAM_PROXY:
        logger.info("Используется прокси для Telegram API")
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    try:
        me = await bot.get_me(request_timeout=SESSION_TIMEOUT)
        logger.info("✅ Подключение OK: @%s", me.username)
    except TelegramNetworkError:
        logger.error(
            "Нет связи с api.telegram.org (таймаут).\n"
            "  • Проверь интернет / VPN\n"
            "  • Отключи блокировку Telegram\n"
            "  • Повтори: ./bot.sh"
        )
        await bot.session.close()
        sys.exit(1)

    await bot.delete_webhook(drop_pending_updates=True)
    await setup_commands(bot)

    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    dp.message.middleware(ActivityMiddleware())
    dp.include_router(setup_routers())

    asyncio.create_task(background_loop(bot))

    logger.info("🤖 Бот запущен — scoring, analytics, reminders, cashflow")
    if REQUIRED_CHANNEL:
        logger.info("📢 Обязательная подписка: %s", REQUIRED_CHANNEL)
    try:
        await dp.start_polling(bot, handle_signals=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
