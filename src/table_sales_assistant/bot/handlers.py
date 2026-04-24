from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from table_sales_assistant.bot.keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        'Привет! Я демо-ассистент по подбору регулируемых столов.',
        reply_markup=main_menu_keyboard(),
    )
