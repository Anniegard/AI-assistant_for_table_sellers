import pytest

from table_sales_assistant.assistant.free_text_parser import (
    ACTIVE_STEP_BUDGET,
    ACTIVE_STEP_HEIGHT,
    parse_budget_from_text,
    parse_signals,
)


@pytest.mark.parametrize(
    "text,expected_min,expected_max",
    [
        ("до 50000", None, 50000),
        ("до 50к", None, 50000),
        ("50к", None, 50000),
        ("50000", None, 50000),
        ("50000 рублей", None, 50000),
        ("бюджет 50000", None, 50000),
        ("от 50000 до 80000", 50000, 80000),
        ("от 50 до 80к", 50000, 80000),
        ("50-80к", 50000, 80000),
        ("50 000 - 80 000", 50000, 80000),
        ("примерно 70к", None, 70000),
        ("80 тыс", None, 80000),
    ],
)
def test_parse_budget_variants(
    text: str, expected_min: int | None, expected_max: int | None
) -> None:
    lo, hi, _ = parse_budget_from_text(text)
    assert lo == expected_min
    assert hi == expected_max


def test_parse_height_context_budget_step() -> None:
    s = parse_signals("178", active_step=ACTIVE_STEP_BUDGET)
    assert s.height_cm is None
    s2 = parse_signals("178", active_step=ACTIVE_STEP_HEIGHT)
    assert s2.height_cm == 178


def test_parse_monitors_words() -> None:
    from table_sales_assistant.assistant.free_text_parser import ACTIVE_STEP_MONITORS

    assert parse_signals("два монитора", active_step=None).monitors_count == 2
    assert parse_signals("три монитора", active_step=None).monitors_count == 3
    assert parse_signals("2", active_step=ACTIVE_STEP_MONITORS).monitors_count == 2


def test_parse_size_and_pc() -> None:
    s = parse_signals("стол 140x70", active_step=None)
    assert s.preferred_width_cm == 140
    assert s.preferred_depth_cm == 70
    s2 = parse_signals("системник на столе", active_step=None)
    assert s2.has_pc_on_table is True
    s3 = parse_signals("только ноутбук", active_step=None)
    assert s3.has_pc_on_table is False


def test_parse_scenario_russian() -> None:
    assert parse_signals("для игр", active_step=None).internal_scenario == "gaming"
    assert parse_signals("для офиса", active_step=None).internal_scenario == "office"
    assert parse_signals("для учебы", active_step=None).internal_scenario == "study"
