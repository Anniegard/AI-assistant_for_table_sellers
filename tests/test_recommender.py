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


def test_recommendation_excludes_accessories() -> None:
    products = ProductRepository(Path("data/products.sample.json")).load_products()
    recommender = ProductRecommender()
    result = recommender.recommend(
        products,
        RecommendationQuery(
            budget=50000,
            user_height_cm=190,
            monitors_count=2,
            use_case="home_office",
        ),
    )
    assert result
    assert all(product.category != "accessory" for product in result)
    assert all(product.name != "CableTray Pro" for product in result)


def test_budget_is_strict_when_matches_exist() -> None:
    products = ProductRepository(Path("data/products.sample.json")).load_products()
    recommender = ProductRecommender()
    result = recommender.recommend(
        products,
        RecommendationQuery(
            budget=50000,
            user_height_cm=190,
            monitors_count=2,
            use_case="home_office",
        ),
    )
    assert result
    assert any(product.price <= 50000 for product in result)
    assert all(product.price <= 50000 for product in result)


def test_strict_budget_returns_empty_when_all_above_budget() -> None:
    products = ProductRepository(Path("data/products.sample.json")).load_products()
    recommender = ProductRecommender()
    result = recommender.recommend(
        products,
        RecommendationQuery(
            budget=20000,
            user_height_cm=190,
            monitors_count=2,
            use_case="home_office",
            strict_budget=True,
        ),
    )
    assert result == []
