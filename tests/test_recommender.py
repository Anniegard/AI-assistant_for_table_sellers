from pathlib import Path

from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.repository import ProductRepository


def test_recommender_returns_products_within_budget() -> None:
    products = ProductRepository(Path('data/products.sample.json')).load_products()
    recommender = ProductRecommender()

    result = recommender.recommend(
        products,
        RecommendationQuery(
            budget=50000,
            user_height_cm=178,
            monitors_count=2,
            motors_preference=2,
        ),
    )

    assert result
    assert all(product.price <= 50000 for product in result)
    assert all(product.motors_count == 2 for product in result)
