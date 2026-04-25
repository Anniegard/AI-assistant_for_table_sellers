"""Backward-compatible parsing helpers; logic lives in free_text_parser."""

from table_sales_assistant.assistant.free_text_parser import (
    parse_budget_from_text,
    parse_has_pc_on_table,
    parse_height_cm,
    parse_internal_scenario,
    parse_monitors_with_step,
)

USE_CASE_KEYWORDS: dict[str, str] = {
    "дом": "home_office",
    "офис": "office",
    "разработ": "gaming",
    "it": "gaming",
    "игр": "gaming",
    "учеб": "study",
    "руковод": "office",
    "инженер": "gaming",
}


def extract_height_cm(text: str) -> int | None:
    return parse_height_cm(text, active_step=None)


def extract_monitors_count(text: str) -> int | None:
    return parse_monitors_with_step(text, active_step=None)


def extract_budget_range(text: str) -> tuple[int | None, int | None]:
    lo, hi, _ = parse_budget_from_text(text)
    return lo, hi


def extract_use_case(text: str) -> str | None:
    internal = parse_internal_scenario(text)
    if internal:
        return internal
    lowered = text.lower()
    for key, mapped in USE_CASE_KEYWORDS.items():
        if key in lowered:
            return mapped
    return None


def extract_has_pc_case(text: str) -> bool | None:
    return parse_has_pc_on_table(text)
