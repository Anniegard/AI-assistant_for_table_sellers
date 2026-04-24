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
        "Мне нужен стол для дома, рост 185, два монитора, бюджет до 70к",
        context,
    )
    assert response.goal == AssistantGoal.RECOMMEND
    assert context.known_params.height_cm == 185
    assert context.known_params.monitors_count == 2
    assert context.known_params.budget_max == 70000
    assert context.recommended_products


def test_dialogue_service_starts_lead_flow_on_request() -> None:
    service = _build_service()
    context = DialogueContext(user_id=2, known_params=KnownClientParams())
    response = service.handle("Оставь заявку", context)
    assert response.start_lead_flow is True
