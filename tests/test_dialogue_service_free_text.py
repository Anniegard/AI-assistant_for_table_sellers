from pathlib import Path

from table_sales_assistant.ai.client import OpenAIClient
from table_sales_assistant.assistant.collection import (
    ASK_MONITORS_STEP_TEXT,
    ASK_PC_STEP_TEXT,
    ASK_SIZE_STEP_TEXT,
)
from table_sales_assistant.assistant.dialogue_service import DialogueService
from table_sales_assistant.assistant.models import AssistantGoal, DialogueContext, KnownClientParams
from table_sales_assistant.assistant.parsing import extract_budget_range
from table_sales_assistant.catalog.recommender import ProductRecommender
from table_sales_assistant.catalog.repository import ProductRepository
from table_sales_assistant.services.explanation_service import ExplanationService
from table_sales_assistant.services.faq_service import FAQService
from table_sales_assistant.services.recommendation_service import RecommendationService


def _build_service() -> DialogueService:
    recommendation_service = RecommendationService(
        repository=ProductRepository(Path("data/products.sample.json")),
        recommender=ProductRecommender(),
    )
    faq_service = FAQService(Path("data/knowledge"))
    explanation_service = ExplanationService(OpenAIClient(""))
    return DialogueService(recommendation_service, faq_service, explanation_service)


def test_recommendation_response_has_no_internal_scenario_tokens() -> None:
    service = _build_service()
    context = DialogueContext(user_id=99, known_params=KnownClientParams())
    response = service.handle(
        "рост 178 бюджет 60000 для офиса 2 монитора только ноутбук 140x70", context
    )
    assert response.goal == AssistantGoal.RECOMMEND
    lower = response.text.lower()
    assert "home_office" not in lower
    assert "it_work" not in lower
    assert "family_workspace" not in lower


def test_dialogue_service_extracts_params_and_recommends() -> None:
    service = _build_service()
    context = DialogueContext(user_id=1, known_params=KnownClientParams())
    response = service.handle(
        "рост 180 бюджет 50000 для дома",
        context,
    )
    assert response.goal in {AssistantGoal.RECOMMEND, AssistantGoal.ASK_MISSING_PARAM}
    assert context.known_params.height_cm == 180
    assert context.known_params.budget_max == 50000
    assert context.known_params.use_case == "home_office"
    assert response.text
    assert "cabletray pro" not in response.text.lower()


def test_parse_budget_from_compact_free_text() -> None:
    service = _build_service()
    context = DialogueContext(user_id=10, known_params=KnownClientParams())
    service.handle("рост 190 бюджет 50000 для дома", context)
    assert context.known_params.height_cm == 190
    assert context.known_params.budget_max == 50000
    assert context.known_params.use_case == "home_office"


def test_dialogue_service_starts_lead_flow_on_request() -> None:
    service = _build_service()
    context = DialogueContext(user_id=2, known_params=KnownClientParams())
    response = service.handle("Оставь заявку", context)
    assert response.start_lead_flow is True


def test_dialogue_service_accumulates_params_between_messages() -> None:
    service = _build_service()
    context = DialogueContext(user_id=3, known_params=KnownClientParams())
    first = service.handle("рост 190", context)
    second = service.handle("бюджет 50000", context)
    assert first.goal == AssistantGoal.ASK_MISSING_PARAM
    assert second.goal in {AssistantGoal.RECOMMEND, AssistantGoal.ASK_MISSING_PARAM}
    assert context.known_params.height_cm == 190
    assert context.known_params.budget_max == 50000


def test_dialogue_service_does_not_block_without_monitors() -> None:
    service = _build_service()
    context = DialogueContext(user_id=4, known_params=KnownClientParams())
    response = service.handle("рост 180 бюджет 50000 для дома", context)
    assert response.goal == AssistantGoal.ASK_MISSING_PARAM
    assert response.text == ASK_MONITORS_STEP_TEXT
    assert "уточните бюджет" not in response.text.lower()
    assert context.known_params.height_cm == 180
    assert context.known_params.budget_max == 50000
    assert context.known_params.use_case == "home_office"
    assert not context.recommended_products


def test_faq_question_has_priority_over_missing_params() -> None:
    service = _build_service()
    context = DialogueContext(
        user_id=6,
        known_params=KnownClientParams(height_cm=190, budget_max=50000, use_case="home_office"),
    )
    response = service.handle("А чем два мотора лучше?", context)
    assert response.goal == AssistantGoal.ANSWER_QUESTION
    assert "два мотора" in response.text.lower()
    assert "укажите бюджет" not in response.text.lower()


def test_budget_parsing_variants() -> None:
    variants = [
        "до 50 000",
        "50к",
        "50 тыс",
        "50000 рублей",
        "бюджет 50000",
    ]
    for text in variants:
        budget_min, budget_max = extract_budget_range(text)
        assert budget_min is None
        assert budget_max == 50000


def test_lead_request_uses_existing_context() -> None:
    service = _build_service()
    context = DialogueContext(user_id=7, known_params=KnownClientParams())
    first_response = service.handle(
        "рост 190 бюджет 50000 для дома 2 монитора только ноутбук 140x70",
        context,
    )
    assert first_response.goal == AssistantGoal.RECOMMEND
    assert context.recommended_products

    lead_response = service.handle("Оставь заявку", context)
    assert lead_response.start_lead_flow is True
    assert "как вас зовут" in lead_response.text.lower()
    assert context.known_params.height_cm == 190
    assert context.known_params.budget_max == 50000
    assert context.recommended_products


def test_dialogue_context_stores_recent_user_and_assistant_messages() -> None:
    service = _build_service()
    context = DialogueContext(user_id=5, known_params=KnownClientParams())
    for idx in range(12):
        service.handle(f"рост 19{idx} бюджет 50000", context)
    history = context.get_recent_history(limit=10)
    assert len(history) == 10
    assert {item.role for item in history} == {"user", "assistant"}


def test_cheaper_request_does_not_repeat_same_products() -> None:
    service = _build_service()
    context = DialogueContext(user_id=11, known_params=KnownClientParams())
    first = service.handle(
        "рост 190 бюджет 50000 для дома 2 монитора системник на столе 140x70", context
    )
    first_ids = list(context.recommended_products)
    assert first.goal == AssistantGoal.RECOMMEND
    assert first_ids

    second = service.handle("давай дешевле", context)
    second_ids = list(context.recommended_products)
    assert second.goal == AssistantGoal.ASK_MISSING_PARAM
    assert "в каком бюджете теперь смотреть" in second.text.lower()
    assert context.awaiting_budget_after_cheaper is True
    assert second_ids == first_ids


def test_guided_flow_asks_monitors_after_scenario_height_budget() -> None:
    service = _build_service()
    context = DialogueContext(user_id=18, known_params=KnownClientParams())
    response = service.handle("рост 180 бюджет 50000 для дома", context)
    assert response.goal == AssistantGoal.ASK_MISSING_PARAM
    assert response.text == ASK_MONITORS_STEP_TEXT
    assert context.known_params.height_cm == 180
    assert context.known_params.budget_max == 50000
    assert context.known_params.use_case == "home_office"


def test_guided_flow_asks_pc_after_monitors() -> None:
    service = _build_service()
    context = DialogueContext(
        user_id=19,
        known_params=KnownClientParams(height_cm=180, budget_max=50000, use_case="home_office"),
    )
    response = service.handle("2 монитора", context)
    assert response.goal == AssistantGoal.ASK_MISSING_PARAM
    assert response.text == ASK_PC_STEP_TEXT
    assert context.known_params.monitors_count == 2


def test_guided_flow_asks_size_after_pc() -> None:
    service = _build_service()
    context = DialogueContext(
        user_id=20,
        known_params=KnownClientParams(
            height_cm=180,
            budget_max=50000,
            use_case="home_office",
            monitors_count=2,
        ),
    )
    response = service.handle("системник на столе", context)
    assert response.goal == AssistantGoal.ASK_MISSING_PARAM
    assert response.text == ASK_SIZE_STEP_TEXT
    assert context.known_params.has_pc_case is True


def test_guided_flow_recommends_after_size_answer() -> None:
    service = _build_service()
    context = DialogueContext(
        user_id=21,
        known_params=KnownClientParams(
            height_cm=180,
            budget_max=50000,
            use_case="home_office",
            monitors_count=2,
            has_pc_case=False,
        ),
    )
    response = service.handle("140x70", context)
    assert response.goal == AssistantGoal.RECOMMEND
    assert context.known_params.preferred_width_cm == 140
    assert context.known_params.preferred_depth_cm == 70
    assert context.recommended_products


def test_cheaper_without_budget_asks_for_new_budget() -> None:
    service = _build_service()
    context = DialogueContext(
        user_id=22,
        known_params=KnownClientParams(
            height_cm=180,
            budget_max=70000,
            use_case="home_office",
            monitors_count=2,
            has_pc_case=False,
            preferred_width_cm=140,
            preferred_depth_cm=70,
        ),
        recommended_products=["desk_basic_01"],
        guide_active=False,
    )
    response = service.handle("давай дешевле", context)
    assert response.goal == AssistantGoal.ASK_MISSING_PARAM
    assert "в каком бюджете теперь смотреть" in response.text.lower()
    assert context.awaiting_budget_after_cheaper is True
    assert context.recommended_products == ["desk_basic_01"]


def test_cheaper_with_budget_recalculates() -> None:
    service = _build_service()
    context = DialogueContext(user_id=23, known_params=KnownClientParams())
    first = service.handle(
        "рост 180 бюджет 90000 для дома 2 монитора только ноутбук 140x70",
        context,
    )
    first_ids = list(context.recommended_products)
    assert first.goal == AssistantGoal.RECOMMEND
    response = service.handle("давай до 50к", context)
    assert response.goal == AssistantGoal.RECOMMEND
    assert context.known_params.budget_max == 50000
    assert context.awaiting_budget_after_cheaper is False
    assert context.recommended_products
    assert context.guide_active is False
    assert first_ids


def test_budget_answer_after_cheaper_prompt_recalculates() -> None:
    service = _build_service()
    context = DialogueContext(user_id=24, known_params=KnownClientParams())
    first = service.handle(
        "рост 180 бюджет 90000 для дома 2 монитора только ноутбук 140x70",
        context,
    )
    assert first.goal == AssistantGoal.RECOMMEND
    ask = service.handle("давай дешевле", context)
    assert ask.goal == AssistantGoal.ASK_MISSING_PARAM
    assert context.awaiting_budget_after_cheaper is True
    response = service.handle("40-60к", context)
    assert response.goal == AssistantGoal.RECOMMEND
    assert context.known_params.budget_min == 40000
    assert context.known_params.budget_max == 60000
    assert context.awaiting_budget_after_cheaper is False


def test_compare_request_uses_recommended_products() -> None:
    service = _build_service()
    context = DialogueContext(user_id=14, known_params=KnownClientParams())
    first = service.handle(
        "рост 190 бюджет 50000 для дома 2 монитора только ноутбук 140x70",
        context,
    )
    assert first.goal == AssistantGoal.RECOMMEND
    first_ids = list(context.recommended_products)
    assert first_ids

    compare = service.handle("сравни варианты", context)
    assert compare.goal == AssistantGoal.COMPARE
    assert "сравнение по последним вариантам" in compare.text.lower()
    assert "следующий шаг:" not in compare.text.lower()
    assert context.recommended_products == first_ids


def test_recommendation_template_is_compact_without_confidence_and_cta_hint() -> None:
    service = _build_service()
    context = DialogueContext(user_id=15, known_params=KnownClientParams())
    response = service.handle(
        "рост 182 бюджет 80000 для дома 2 монитора только ноутбук 140x70", context
    )
    assert response.goal == AssistantGoal.RECOMMEND
    assert "уверенность:" not in response.text.lower()
    assert "следующий шаг:" not in response.text.lower()
    assert "рекомендую:" in response.text.lower()


def test_faq_uses_contextual_template() -> None:
    service = _build_service()
    context = DialogueContext(
        user_id=16,
        known_params=KnownClientParams(
            height_cm=185,
            budget_max=90000,
            monitors_count=2,
            use_case="it_work",
        ),
    )
    response = service.handle("какая гарантия?", context)
    assert response.goal == AssistantGoal.ANSWER_QUESTION
    assert "с учетом ваших параметров" in response.text.lower()
    assert "следующий шаг:" not in response.text.lower()


def test_fallback_never_returns_empty_no_match_message() -> None:
    service = _build_service()
    context = DialogueContext(user_id=17, known_params=KnownClientParams())
    response = service.handle(
        "подбери стол: рост 230 бюджет 30000 для дома 2 монитора системник на столе 200x90",
        context,
    )
    assert "точного совпадения сейчас нет" in response.text.lower()
    assert "что ограничивает подбор" in response.text.lower()
    assert "ближайшие альтернативы" in response.text.lower()
    assert response.cta == "Позвать менеджера"


def test_accessory_can_be_recommended_only_for_accessory_intent() -> None:
    service = _build_service()
    context = DialogueContext(user_id=12, known_params=KnownClientParams())
    accessory_response = service.handle("какие аксессуары нужны для стола?", context)
    assert "из аксессуаров можно рассмотреть" in accessory_response.text.lower()

    desk_context = DialogueContext(user_id=13, known_params=KnownClientParams())
    desk_response = service.handle(
        "подбери стол рост 190 бюджет 50000 для дома 2 монитора только ноутбук 140x70",
        desk_context,
    )
    assert desk_response.goal == AssistantGoal.RECOMMEND
    assert "cabletray pro" not in desk_response.text.lower()
