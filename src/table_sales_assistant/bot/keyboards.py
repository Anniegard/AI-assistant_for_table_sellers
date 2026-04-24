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


def recommendation_ready_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Оставить заявку по этим вариантам")],
            [KeyboardButton(text="Оставить заявку")],
            [KeyboardButton(text="Подобрать стол")],
            [KeyboardButton(text="Частые вопросы")],
            [KeyboardButton(text="Демо-режим")],
        ],
        resize_keyboard=True,
    )
