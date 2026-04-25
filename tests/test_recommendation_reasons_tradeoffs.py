from pathlib import Path

from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.repository import ProductRepository


def test_recommendation_contains_best_for_and_reasoning_fields() -> None:
    products = ProductRepository(Path("data/products.sample.json")).load_products()
    results = ProductRecommender().recommend_scored(
        products,
        RecommendationQuery(
            budget=50000,
            user_height_cm=180,
            monitors_count=2,
            use_case="it_work",
            has_pc_case=True,
        ),
    )
    assert results
    assert all(item.best_for for item in results)
    assert all(item.reasons for item in results)
    assert all(item.tradeoffs is not None for item in results)
