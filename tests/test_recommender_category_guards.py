from table_sales_assistant.catalog.models import Product
from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery


def _base_product(product_id: str, category: str) -> Product:
    return Product(
        id=product_id,
        name=product_id,
        category=category,
        segment="demo",
        price=50000,
        min_height_cm=70,
        max_height_cm=120,
        tabletop_width_cm=140,
        tabletop_depth_cm=70,
        motors_count=2,
        lifting_capacity_kg=120,
        material="ЛДСП",
        colors=["black"],
        use_cases=["home_office"],
        recommended_user_height_min_cm=160,
        recommended_user_height_max_cm=195,
        product_url="https://example.com",
        in_stock=True,
        short_description="demo",
    )


def test_unknown_not_in_main_recommendations() -> None:
    recommender = ProductRecommender()
    products = [_base_product("unknown-1", "unknown"), _base_product("desk-1", "adjustable_desk")]
    result = recommender.recommend(
        products,
        RecommendationQuery(budget=80000, user_height_cm=180, monitors_count=2),
    )
    assert result
    assert all(product.category == "adjustable_desk" for product in result)


def test_accessory_not_in_desk_recommendations() -> None:
    recommender = ProductRecommender()
    products = [_base_product("acc-1", "accessory"), _base_product("desk-1", "adjustable_desk")]
    result = recommender.recommend(
        products,
        RecommendationQuery(budget=80000, user_height_cm=180, monitors_count=2),
    )
    assert result
    assert all(product.category == "adjustable_desk" for product in result)
