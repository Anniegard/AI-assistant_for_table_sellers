from dataclasses import dataclass

from table_sales_assistant.catalog.models import Product


@dataclass(slots=True)
class RecommendationQuery:
    budget: int | None = None
    user_height_cm: int | None = None
    monitors_count: int | None = None
    motors_preference: int | None = None
    use_case: str | None = None


class ProductRecommender:
    def recommend(
        self, products: list[Product], query: RecommendationQuery, limit: int = 3
    ) -> list[Product]:
        filtered = []
        for product in products:
            if query.budget is not None and product.price > query.budget:
                continue
            if query.user_height_cm is not None:
                if not (
                    product.recommended_user_height_min_cm
                    <= query.user_height_cm
                    <= product.recommended_user_height_max_cm
                ):
                    continue
            if query.monitors_count is not None:
                min_width = 100 if query.monitors_count >= 2 else 80
                if product.tabletop_width_cm < min_width:
                    continue
            if (
                query.motors_preference is not None
                and product.motors_count != query.motors_preference
            ):
                continue
            if query.use_case and query.use_case not in product.use_cases:
                continue
            if not product.in_stock:
                continue
            filtered.append(product)

        filtered.sort(key=lambda item: (item.price, -item.lifting_capacity_kg))
        return filtered[:limit]
