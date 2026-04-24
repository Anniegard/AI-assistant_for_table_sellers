from pathlib import Path

from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.repository import ProductRepository


def test_recommender_scored_returns_fit_score_and_reasons() -> None:
    products = ProductRepository(Path("data/products.sample.json")).load_products()
    recommender = ProductRecommender()
    results = recommender.recommend_scored(
        products,
        RecommendationQuery(budget=80000, user_height_cm=185, monitors_count=2, use_case="it_work"),
    )
    assert results
    assert all(result.fit_score > 0 for result in results)
    assert all(result.reasons for result in results)


def test_recommender_excludes_out_of_stock_by_hard_filter() -> None:
    products = ProductRepository(Path("data/products.sample.json")).load_products()
    recommender = ProductRecommender()
    results = recommender.recommend_scored(products, RecommendationQuery(budget=150000))
    assert all(result.product.in_stock for result in results)
