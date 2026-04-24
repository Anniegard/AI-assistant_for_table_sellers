from aiogram import Router

from table_sales_assistant.bot.handlers import router as main_router


def build_main_router() -> Router:
    return main_router
