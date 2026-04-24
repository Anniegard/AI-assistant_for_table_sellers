from pathlib import Path

from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.repository import ProductRepository


def test_recommendation_contains_tradeoffs_and_best_for() -> None:
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
    assert any(item.tradeoffs for item in results)
