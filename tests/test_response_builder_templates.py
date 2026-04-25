from table_sales_assistant.assistant.models import DialogueIntent
from table_sales_assistant.assistant.response_builder import ResponseBuilder


def test_product_recommendation_template_contains_required_blocks() -> None:
    response = ResponseBuilder.recommendation(
        intro_lines=["Понял: рост 182 см, бюджет до 80 000 ₽."],
        items=[
            {
                "name": "Demo Desk 1",
                "price": "79 900 ₽",
                "reason": "Подходит под два монитора",
                "tradeoff": "Ширина меньше желаемой",
                "confidence": "high",
            }
        ],
        cta="Сравнить варианты",
        intent=DialogueIntent.RECOMMEND,
    )
    text = response.text.lower()
    assert "рекомендую:" in text
    assert "demo desk 1 — 79 900 ₽".lower() in text
    assert "подходит под два монитора" in text
    assert "важно учесть: ширина меньше желаемой" in text
    assert "почему подходит:" not in text
    assert "ограничения:" not in text
    assert "уверенность:" not in text
    assert "следующий шаг:" not in text
    assert response.cta == "Сравнить варианты"


def test_no_exact_match_template_contains_alternatives_and_blocker() -> None:
    response = ResponseBuilder.no_exact_match(
        blocking_constraint="жесткий бюджет",
        alternatives=["Ослабить лимит бюджета", "Позвать менеджера"],
        cta="Позвать менеджера",
        intent=DialogueIntent.UNKNOWN,
    )
    text = response.text.lower()
    assert "точного совпадения сейчас нет" in text
    assert "что ограничивает подбор: жесткий бюджет" in text
    assert "ближайшие альтернативы" in text
    assert response.cta == "Позвать менеджера"
