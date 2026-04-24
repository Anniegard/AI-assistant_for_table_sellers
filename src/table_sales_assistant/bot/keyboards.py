from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Подобрать стол')],
            [KeyboardButton(text='Задать вопрос')],
            [KeyboardButton(text='Сравнить варианты')],
            [KeyboardButton(text='Оставить заявку')],
            [KeyboardButton(text='Позвать менеджера')],
            [KeyboardButton(text='Начать заново')],
            [KeyboardButton(text='Отмена')],
            [KeyboardButton(text='Демо-режим')],
        ],
        resize_keyboard=True,
    )


def recommendation_ready_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Оставить заявку по этим вариантам")],
            [KeyboardButton(text="Сравнить варианты")],
            [KeyboardButton(text="Почему этот стол?")],
            [KeyboardButton(text="Есть дешевле?")],
            [KeyboardButton(text="Оставить заявку")],
            [KeyboardButton(text="Подобрать стол")],
            [KeyboardButton(text="Задать вопрос")],
            [KeyboardButton(text="Демо-режим")],
        ],
        resize_keyboard=True,
    )
