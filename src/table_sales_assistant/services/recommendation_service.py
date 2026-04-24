from typing import Protocol

from table_sales_assistant.catalog.recommender import (
    ProductRecommender,
    RecommendationQuery,
    RecommendationResult,
)


class CatalogRepository(Protocol):
    def load_products(self): ...


class RecommendationService:
    def __init__(self, repository: CatalogRepository, recommender: ProductRecommender) -> None:
        self.repository = repository
        self.recommender = recommender

    def get_recommendations(self, query: RecommendationQuery):
        products = self.repository.load_products()
        return self.recommender.recommend(products=products, query=query)

    def get_ranked_recommendations(self, query: RecommendationQuery) -> list[RecommendationResult]:
        products = self.repository.load_products()
        return self.recommender.recommend_scored(products=products, query=query)

    def get_products_by_ids(self, product_ids: list[str]):
        ids = set(product_ids)
        if not ids:
            return []
        products = self.repository.load_products()
        return [product for product in products if product.id in ids]
