from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Подобрать стол')],
            [KeyboardButton(text='Частые вопросы')],
            [KeyboardButton(text='Оставить заявку')],
            [KeyboardButton(text='Демо-режим')],
        ],
        resize_keyboard=True,
    )
