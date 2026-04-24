from pathlib import Path

from table_sales_assistant.ai.client import OpenAIClient
from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.repository import ProductRepository
from table_sales_assistant.services.explanation_service import ExplanationService
from table_sales_assistant.services.recommendation_service import RecommendationService


def test_explanations_keys_match_only_catalog_products() -> None:
    repository = ProductRepository(Path("data/products.sample.json"))
    service = RecommendationService(repository, ProductRecommender())
    products = service.get_recommendations(RecommendationQuery(budget=70000, user_height_cm=180))
    explanations = ExplanationService(OpenAIClient("")).explain_products(products, query_context={})
    catalog_ids = {item.id for item in repository.load_products()}
    assert set(explanations.keys()).issubset(catalog_ids)
