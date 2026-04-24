from table_sales_assistant.bot.keyboards import main_menu_keyboard
from table_sales_assistant.bot.router_factory import build_main_router


def test_main_menu_contains_required_buttons() -> None:
    keyboard = main_menu_keyboard()
    labels = [button.text for row in keyboard.keyboard for button in row]
    assert labels == ["Подобрать стол", "Частые вопросы", "Оставить заявку", "Демо-режим"]


def test_router_factory_returns_router() -> None:
    router = build_main_router()
    assert router is not None
