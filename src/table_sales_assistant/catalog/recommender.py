from dataclasses import dataclass

from table_sales_assistant.catalog.models import Product


@dataclass(slots=True)
class RecommendationQuery:
    budget: int | None = None
    user_height_cm: int | None = None
    monitors_count: int | None = None
    motors_preference: int | None = None
    use_case: str | None = None
    has_pc_case: bool | None = None


@dataclass(slots=True)
class RecommendationResult:
    product: Product
    fit_score: float
    reasons: list[str]
    tradeoffs: list[str]
    best_for: str


class ProductRecommender:
    def _hard_filter(self, product: Product, query: RecommendationQuery) -> bool:
        if not product.in_stock:
            return False
        if query.budget is not None and product.price > int(query.budget * 1.2):
            return False
        if query.user_height_cm is not None and not (
            product.recommended_user_height_min_cm
            <= query.user_height_cm
            <= product.recommended_user_height_max_cm
        ):
            return False
        if query.use_case and query.use_case not in product.use_cases:
            return False
        if query.motors_preference is not None and product.motors_count != query.motors_preference:
            return False
        return True

    def _score(self, product: Product, query: RecommendationQuery) -> RecommendationResult:
        score = 50.0
        reasons: list[str] = []
        tradeoffs: list[str] = []

        if query.budget is not None:
            budget_delta = query.budget - product.price
            if budget_delta >= 0:
                score += max(0, min(15, budget_delta / 4000))
                reasons.append("Укладывается в указанный бюджет")
            else:
                score -= 12
                tradeoffs.append("Немного выше целевого бюджета")

        if query.monitors_count is not None:
            expected_width = 140 if query.monitors_count >= 2 else 100
            if product.tabletop_width_cm >= expected_width:
                score += 10
                reasons.append("Подходящая ширина под количество мониторов")
            else:
                score -= 8
                tradeoffs.append("Может быть тесно для вашей конфигурации мониторов")

        if query.has_pc_case:
            if product.motors_count >= 2 and product.lifting_capacity_kg >= 100:
                score += 10
                reasons.append("Есть запас устойчивости и нагрузки под системный блок")
            else:
                score -= 6
                tradeoffs.append("Ограниченный запас по нагрузке для тяжелого сетапа")

        if query.motors_preference is not None:
            if product.motors_count == query.motors_preference:
                score += 6
                reasons.append("Совпадает с предпочтением по моторам")
            else:
                score -= 4
                tradeoffs.append("Не совпадает с предпочтением по моторам")

        if query.use_case and query.use_case in product.use_cases:
            score += 8
            reasons.append("Модель подходит под ваш сценарий использования")

        if product.motors_count >= 2:
            score += 3
        if product.lifting_capacity_kg >= 110:
            score += 3

        if not reasons:
            reasons.append("Сбалансированный вариант по ключевым параметрам")
        if product.motors_count == 1:
            tradeoffs.append("Один мотор: меньше запас по стабильности под нагрузкой")

        best_for = "универсального домашнего и рабочего сценария"
        if "it_work" in product.use_cases:
            best_for = "сетапов с двумя мониторами и длительной работой"
        elif "executive_office" in product.use_cases:
            best_for = "просторного премиального рабочего места"
        elif "study" in product.use_cases:
            best_for = "учебы и базового домашнего офиса"

        return RecommendationResult(
            product=product,
            fit_score=round(score, 2),
            reasons=reasons[:3],
            tradeoffs=tradeoffs[:2],
            best_for=best_for,
        )

    def recommend_scored(
        self, products: list[Product], query: RecommendationQuery, limit: int = 3
    ) -> list[RecommendationResult]:
        filtered = [product for product in products if self._hard_filter(product, query)]
        results = [self._score(product, query) for product in filtered]
        results.sort(
            key=lambda item: (
                -item.fit_score,
                item.product.price,
                -item.product.lifting_capacity_kg,
            )
        )
        return results[:limit]

    def recommend(
        self, products: list[Product], query: RecommendationQuery, limit: int = 3
    ) -> list[Product]:
        return [
            item.product
            for item in self.recommend_scored(products=products, query=query, limit=limit)
        ]
