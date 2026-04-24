from pathlib import Path

from table_sales_assistant.ai.client import OpenAIClient
from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.repository import ProductRepository
from table_sales_assistant.services.explanation_service import ExplanationService
from table_sales_assistant.services.recommendation_service import RecommendationService


def test_explanation_fallback_when_ai_disabled() -> None:
    repository = ProductRepository(Path("data/products.sample.json"))
    recommendation_service = RecommendationService(repository, ProductRecommender())
    products = recommendation_service.get_recommendations(
        RecommendationQuery(budget=50000, user_height_cm=178, monitors_count=2, motors_preference=2)
    )
    assert products

    explanations = ExplanationService(OpenAIClient("")).explain_products(products, query_context={})
    assert explanations
    assert set(explanations.keys()) == {item.id for item in products}
