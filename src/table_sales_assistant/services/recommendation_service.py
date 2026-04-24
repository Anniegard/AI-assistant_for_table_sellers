from table_sales_assistant.catalog.recommender import (
    ProductRecommender,
    RecommendationQuery,
    RecommendationResult,
)
from table_sales_assistant.catalog.repository import ProductRepository


class RecommendationService:
    def __init__(self, repository: ProductRepository, recommender: ProductRecommender) -> None:
        self.repository = repository
        self.recommender = recommender

    def get_recommendations(self, query: RecommendationQuery):
        products = self.repository.load_products()
        return self.recommender.recommend(products=products, query=query)

    def get_ranked_recommendations(self, query: RecommendationQuery) -> list[RecommendationResult]:
        products = self.repository.load_products()
        return self.recommender.recommend_scored(products=products, query=query)
