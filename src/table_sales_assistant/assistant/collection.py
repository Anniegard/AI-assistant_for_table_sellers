"""Guided collection step order and prompts for desk selection."""

from __future__ import annotations

STEP_SCENARIO = "scenario"
STEP_HEIGHT = "height"
STEP_BUDGET = "budget"
STEP_MONITORS = "monitors"
STEP_PC = "pc_desk"
STEP_SIZE = "size"

COLLECTION_ORDER: tuple[str, ...] = (
    STEP_SCENARIO,
    STEP_HEIGHT,
    STEP_BUDGET,
    STEP_MONITORS,
    STEP_PC,
    STEP_SIZE,
)

ASK_SCENARIO_TEXT = (
    "Для чего вам нужен стол?\n"
    "Можно выбрать вариант или написать своими словами:\n"
    "- Для работы дома\n"
    "- Для офиса\n"
    "- Для игр / тяжёлого сетапа\n"
    "- Для учёбы\n"
    "- Пока не знаю"
)

ASK_HEIGHT_STEP_TEXT = "Какой у вас рост? Например: 178"

ASK_BUDGET_STEP_TEXT = (
    "В каком бюджете смотрим? Можно одной суммой или диапазоном: "
    "до 50 000 ₽, 50-80к, от 50 000 до 80 000."
)

ASK_MONITORS_STEP_TEXT = "Сколько мониторов будет на столе?"

ASK_PC_STEP_TEXT = (
    "Будет ли системный блок стоять на столешнице? Или только мониторы/ноутбук? "
    "(да / нет / не знаю)"
)

ASK_SIZE_STEP_TEXT = (
    "Есть ли ограничение по размеру столешницы или месту в комнате? "
    "Например: 120 см, 140x70 или можно без ограничений."
)

SCENARIO_BUTTON_LABELS: tuple[str, ...] = (
    "Для работы дома",
    "Для офиса",
    "Для игр",
    "Для учёбы",
    "Пока не знаю",
)

LABEL_TO_SCENARIO: dict[str, str] = {
    "для работы дома": "home_office",
    "для дома": "home_office",
    "для офиса": "office",
    "для игр": "gaming",
    "для учёбы": "study",
    "для it / разработки": "gaming",
    "пока не знаю": "unknown",
}


def map_scenario_label(text: str | None) -> str | None:
    if not text:
        return None
    key = text.strip().lower()
    return LABEL_TO_SCENARIO.get(key)
