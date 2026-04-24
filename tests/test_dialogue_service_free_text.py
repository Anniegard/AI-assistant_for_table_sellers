from pathlib import Path

from table_sales_assistant.ai.client import OpenAIClient
from table_sales_assistant.assistant.dialogue_service import DialogueService
from table_sales_assistant.assistant.models import AssistantGoal, DialogueContext, KnownClientParams
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


def test_dialogue_service_extracts_params_and_recommends() -> None:
    service = _build_service()
    context = DialogueContext(user_id=1, known_params=KnownClientParams())
    response = service.handle(
        "рост 190 бюджет 50000 для дома",
        context,
    )
    assert response.goal in {AssistantGoal.RECOMMEND, AssistantGoal.ASK_MISSING_PARAM}
    assert context.known_params.height_cm == 190
    assert context.known_params.budget_max == 50000
    assert context.known_params.use_case == "home_office"
    assert context.recommended_products


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
    response = service.handle("рост 190 бюджет 50000 для дома", context)
    assert response.goal == AssistantGoal.RECOMMEND
    assert "количество мониторов вы не указали" in response.text.lower()


def test_dialogue_context_stores_recent_user_and_assistant_messages() -> None:
    service = _build_service()
    context = DialogueContext(user_id=5, known_params=KnownClientParams())
    for idx in range(12):
        service.handle(f"рост 19{idx} бюджет 50000", context)
    history = context.get_recent_history(limit=10)
    assert len(history) == 10
    assert {item.role for item in history} == {"user", "assistant"}
