from pathlib import Path

from table_sales_assistant.ai.client import OpenAIClient
from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.repository import ProductRepository
from table_sales_assistant.services.explanation_service import ExplanationService
from table_sales_assistant.services.faq_service import FAQService
from table_sales_assistant.services.recommendation_service import RecommendationService


def test_openai_disabled_mode_still_returns_recommendations_and_explanations() -> None:
    recommendation_service = RecommendationService(
        ProductRepository(Path("data/products.sample.json")),
        ProductRecommender(),
    )
    products = recommendation_service.get_recommendations(
        RecommendationQuery(budget=60000, user_height_cm=178, monitors_count=2)
    )
    explanations = ExplanationService(OpenAIClient("")).explain_products(products, query_context={})
    assert products
    assert explanations


def test_faq_works_without_openai() -> None:
    answer = FAQService(Path("data/knowledge")).answer("гарантия")
    assert answer
