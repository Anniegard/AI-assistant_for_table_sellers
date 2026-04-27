"""Guided collection step order and prompts for desk selection."""

from __future__ import annotations

from table_sales_assistant.assistant.models import KnownClientParams

STEP_SCENARIO = "scenario"
STEP_HEIGHT = "height"
STEP_BUDGET = "budget"
STEP_MONITORS = "monitors"
STEP_PC = "pc_desk"
STEP_SIZE = "size"
STEP_CITY = "city"
STEP_ASSEMBLY = "assembly"

COLLECTION_ORDER: tuple[str, ...] = (
    STEP_SCENARIO,
    STEP_HEIGHT,
    STEP_BUDGET,
    STEP_MONITORS,
    STEP_PC,
    STEP_SIZE,
    STEP_CITY,
    STEP_ASSEMBLY,
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

ASK_CITY_STEP_TEXT = "В каком городе нужна доставка?"

ASK_ASSEMBLY_STEP_TEXT = "Нужна ли сборка?"

SCENARIO_BUTTON_LABELS: tuple[str, ...] = (
    "Для работы дома",
    "Для офиса",
    "Для игр",
    "Для учёбы",
    "Пока не знаю",
)

HEIGHT_BUTTON_LABELS: tuple[str, ...] = (
    "До 165 см",
    "165-175 см",
    "176-185 см",
    "186-195 см",
    "Выше 195 см",
    "Ввести вручную",
)

BUDGET_BUTTON_LABELS: tuple[str, ...] = (
    "До 30 000 ₽",
    "30 000-50 000 ₽",
    "50 000-80 000 ₽",
    "80 000+ ₽",
    "Пока не знаю",
)

MONITORS_BUTTON_LABELS: tuple[str, ...] = (
    "1 монитор",
    "2 монитора",
    "3+ монитора",
    "Ноутбук",
    "Ноутбук + монитор",
)

PC_BUTTON_LABELS: tuple[str, ...] = (
    "Да",
    "Нет",
    "Только ноутбук",
    "Системник на полу",
    "Не знаю",
)

SIZE_BUTTON_LABELS: tuple[str, ...] = (
    "Без ограничений",
    "120x60",
    "140x70",
    "160x80",
    "Не знаю",
    "Ввести вручную",
)

CITY_BUTTON_LABELS: tuple[str, ...] = (
    "Москва",
    "Санкт-Петербург",
    "Другой город",
    "Пока не знаю",
)

ASSEMBLY_BUTTON_LABELS: tuple[str, ...] = (
    "Да",
    "Нет",
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


def get_current_collection_step(kp: KnownClientParams) -> str | None:
    if kp.use_case is None:
        return STEP_SCENARIO
    if kp.height_cm is None and not kp.height_unspecified:
        return STEP_HEIGHT
    if kp.budget_max is None and kp.budget_min is None and not kp.budget_unspecified:
        return STEP_BUDGET
    if kp.monitors_count is None and not kp.monitors_unspecified:
        return STEP_MONITORS
    if kp.has_pc_case is None and not kp.pc_unspecified:
        return STEP_PC
    if (
        not kp.no_size_limit
        and kp.max_width_cm is None
        and kp.preferred_width_cm is None
        and not kp.size_unspecified
    ):
        return STEP_SIZE
    if not kp.city:
        return STEP_CITY
    if kp.needs_assembly is None:
        return STEP_ASSEMBLY
    return None
