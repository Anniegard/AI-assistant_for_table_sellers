import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from table_sales_assistant.bot.router_factory import build_main_router
from table_sales_assistant.config import get_settings
from table_sales_assistant.logging_config import setup_logging


async def run_bot() -> None:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not configured. Set it in .env for real Telegram запуск."
        )
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_main_router())
    logger.info("Starting Telegram polling...")
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
