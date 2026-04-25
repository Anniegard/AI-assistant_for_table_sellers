from dataclasses import dataclass

from table_sales_assistant.catalog.models import Product
from table_sales_assistant.catalog.scenario_mapping import catalog_tags_for_scenario


@dataclass(slots=True)
class RecommendationQuery:
    budget: int | None = None
    budget_min_rub: int | None = None
    budget_max_rub: int | None = None
    user_height_cm: int | None = None
    ignore_user_height_hard_filter: bool = False
    monitors_count: int | None = None
    motors_preference: int | None = None
    use_case: str | None = None
    has_pc_case: bool | None = None
    heavy_setup: bool = False
    max_width_cm: int | None = None
    max_depth_cm: int | None = None
    no_size_limit: bool = False
    include_accessories: bool = False
    strict_budget: bool = True
    max_price_override: int | None = None
    min_price_override: int | None = None
    exclude_product_ids: set[str] | None = None


@dataclass(slots=True)
class RecommendationResult:
    product: Product
    fit_score: float
    reasons: list[str]
    tradeoffs: list[str]
    best_for: str
    is_budget_stretch: bool = False


class ProductRecommender:
    _DESK_CATEGORIES = {
        "desk",
        "table",
        "adjustable_desk",
        "single_motor_desk",
        "dual_motor_desk",
        "corner_desk",
    }
    _ACCESSORY_CATEGORIES = {"accessory", "accessories"}
    _FRAME_CATEGORIES = {"frame", "base", "podstolye"}
    _TABLETOP_CATEGORIES = {"tabletop", "stoleshnitsa"}
    _UNKNOWN_CATEGORIES = {"unknown", "other"}

    BUDGET_STRETCH_RATIO = 1.15

    @classmethod
    def _normalized_category(cls, category: str) -> str:
        lowered = (category or "").strip().lower()
        if lowered in cls._ACCESSORY_CATEGORIES:
            return "accessory"
        if lowered in cls._FRAME_CATEGORIES:
            return "frame"
        if lowered in cls._TABLETOP_CATEGORIES:
            return "tabletop"
        if lowered in cls._DESK_CATEGORIES:
            return "adjustable_desk"
        if lowered in cls._UNKNOWN_CATEGORIES:
            return "unknown"
        return lowered or "unknown"

    @staticmethod
    def _budget_cap(query: RecommendationQuery) -> int | None:
        if query.max_price_override is not None:
            return query.max_price_override
        if query.budget_max_rub is not None:
            return query.budget_max_rub
        return query.budget

    @staticmethod
    def _budget_floor(query: RecommendationQuery) -> int | None:
        if query.min_price_override is not None:
            return query.min_price_override
        return query.budget_min_rub

    def _hard_filter(
        self,
        product: Product,
        query: RecommendationQuery,
        *,
        budget_max_rub: int | None,
    ) -> bool:
        if not product.in_stock:
            return False
        normalized_category = self._normalized_category(product.category)
        if query.include_accessories:
            if normalized_category != "accessory":
                return False
        elif normalized_category != "adjustable_desk":
            return False

        if budget_max_rub is not None and budget_max_rub > 0:
            if product.price > 0 and product.price > budget_max_rub:
                return False

        if query.exclude_product_ids and product.id in query.exclude_product_ids:
            return False

        if (
            normalized_category == "adjustable_desk"
            and query.user_height_cm is not None
            and not query.ignore_user_height_hard_filter
            and not (
                product.recommended_user_height_min_cm
                <= query.user_height_cm
                <= product.recommended_user_height_max_cm
            )
        ):
            return False

        if query.motors_preference is not None and product.motors_count != query.motors_preference:
            return False

        if query.max_width_cm is not None and product.tabletop_width_cm > query.max_width_cm:
            return False

        if query.max_depth_cm is not None and product.tabletop_depth_cm > query.max_depth_cm:
            return False

        return True

    def _scenario_overlap_score(self, product: Product, scenario: str | None) -> float:
        if not scenario or scenario == "unknown":
            return 0.0
        tags = catalog_tags_for_scenario(scenario)
        if not tags:
            return 0.0
        overlap = tags.intersection(product.use_cases)
        return float(len(overlap))

    def _score(
        self,
        product: Product,
        query: RecommendationQuery,
        *,
        strict_budget_cap: int | None,
        is_budget_stretch: bool,
    ) -> RecommendationResult:
        score = 50.0
        reasons: list[str] = []
        tradeoffs: list[str] = []

        cap = strict_budget_cap
        floor = self._budget_floor(query)

        if product.price <= 0:
            score -= 4
            tradeoffs.append("Цена не указана в демо-базе")
        elif cap is not None:
            if product.price <= cap:
                budget_delta = cap - product.price
                score += max(0, min(15, budget_delta / 4000))
                reasons.append("Укладывается в указанный бюджет")
            else:
                score -= 5
                if is_budget_stretch:
                    tradeoffs.append(
                        "Этот вариант немного выше бюджета, но я добавил его как запасной, "
                        "потому что он лучше подходит под ваши условия."
                    )
                else:
                    tradeoffs.append("Немного выше целевого бюджета")
        elif product.price <= 0:
            score -= 4
            tradeoffs.append("Цена не указана в демо-базе")

        if floor is not None and product.price > 0:
            if product.price < int(floor * 0.85):
                score -= 6
                tradeoffs.append(
                    "Заметно ниже нижней границы бюджета — возможно, проще комплектация"
                )
            elif cap is not None and floor <= product.price <= cap:
                score += 4
                reasons.append("В пределах заданного бюджетного диапазона")

        scenario = query.use_case
        overlap = self._scenario_overlap_score(product, scenario)
        if scenario and scenario != "unknown":
            if overlap > 0:
                score += 6 + 4 * min(overlap, 2)
                reasons.append("Хорошо бьётся с вашим сценарием использования")
            else:
                score -= 4
                tradeoffs.append(
                    "Не самый типичный вариант для выбранного сценария — смотрите по параметрам"
                )

        score += self._scenario_weight_adjustment(product, query)

        monitors = query.monitors_count or 1
        if monitors >= 2:
            if product.motors_count >= 2:
                score += 10
                reasons.append("Два мотора и запас по устойчивости под два монитора")
            else:
                score -= 8
                tradeoffs.append(
                    "Для двух мониторов чаще спокойнее брать стол с двумя моторами "
                    "и запасом по нагрузке"
                )
            if product.lifting_capacity_kg >= 100:
                score += 5
                reasons.append("Достаточный запас по грузоподъёмности")

        if monitors >= 3:
            if product.tabletop_width_cm >= 150:
                score += 8
                reasons.append("Ширина столешницы лучше под тройной сетап")
            else:
                score -= 10
                tradeoffs.append("На три монитора столешница может быть тесновата")

        heavy = query.heavy_setup or query.has_pc_case is True
        if heavy:
            if product.lifting_capacity_kg >= 100 and product.motors_count >= 2:
                score += 12
                reasons.append("Запас по нагрузке и устойчивости под тяжёлый сетап")
            elif product.motors_count == 1:
                score -= 10
                tradeoffs.append(
                    "Системный блок на столе заметно увеличивает нагрузку — "
                    "лучше модель с запасом по грузоподъёмности и двумя моторами"
                )

        if query.user_height_cm and product.min_height_cm > 0 and product.max_height_cm > 0:
            uh = query.user_height_cm
            if uh < 165 and product.min_height_cm <= 72:
                score += 4
                reasons.append("Удобная минимальная высота для невысокого роста")
            if uh >= 190 and product.max_height_cm >= 120:
                score += 4
                reasons.append("Достаточный запас по высоте в верхнем положении")

        if query.max_width_cm and product.tabletop_width_cm <= query.max_width_cm:
            score += 5
            reasons.append(f"Подходит под ограничение по ширине до {query.max_width_cm} см")

        if not reasons:
            reasons.append("Сбалансированный вариант по ключевым параметрам")
        if product.motors_count == 1 and (monitors >= 2 or heavy):
            tradeoffs.append("Один мотор: меньше запас по стабильности под нагрузкой")

        best_for = self._best_for_line(product)

        return RecommendationResult(
            product=product,
            fit_score=round(score, 2),
            reasons=reasons[:3],
            tradeoffs=tradeoffs[:3],
            best_for=best_for,
            is_budget_stretch=is_budget_stretch,
        )

    @staticmethod
    def _scenario_weight_adjustment(product: Product, query: RecommendationQuery) -> float:
        scenario = query.use_case
        if not scenario or scenario == "unknown":
            return 0.0
        w = product.tabletop_width_cm
        motors = product.motors_count
        load = product.lifting_capacity_kg
        seg = (product.segment or "").lower()
        bonus = 0.0
        if scenario == "study":
            if w <= 140:
                bonus += 7
            if seg == "budget":
                bonus += 5
            if motors == 1 and load <= 80:
                bonus += 3
        elif scenario == "home_office":
            if 120 <= w <= 150:
                bonus += 5
            if motors >= 2:
                bonus += 3
        elif scenario == "office":
            if seg in {"middle", "budget"}:
                bonus += 4
            if motors >= 2:
                bonus += 2
            if seg == "premium":
                bonus -= 3
        elif scenario == "gaming":
            if motors >= 2:
                bonus += 12
            else:
                bonus -= 14
            if load >= 110:
                bonus += 6
            if w >= 160 or query.no_size_limit:
                bonus += 4
        return bonus

    @staticmethod
    def _best_for_line(product: Product) -> str:
        if "it_work" in product.use_cases:
            return "сетапов с двумя мониторами и длительной работой"
        if "executive_office" in product.use_cases:
            return "просторного премиального рабочего места"
        if "study" in product.use_cases:
            return "учёбы и базового домашнего офиса"
        return "универсального домашнего и рабочего сценария"

    def recommend_scored(
        self, products: list[Product], query: RecommendationQuery, limit: int = 3
    ) -> list[RecommendationResult]:
        cap = self._budget_cap(query)
        filtered = [
            product
            for product in products
            if self._hard_filter(product, query, budget_max_rub=cap)
        ]
        results = [
            self._score(
                product,
                query,
                strict_budget_cap=cap,
                is_budget_stretch=False,
            )
            for product in filtered
        ]
        priced_results = [item for item in results if item.product.price > 0]
        if priced_results:
            results = priced_results
        results.sort(
            key=lambda item: (
                -item.fit_score,
                item.product.price,
                -item.product.lifting_capacity_kg,
            )
        )
        out = results[:limit]
        if out or cap is None or cap <= 0:
            return out

        stretch_cap = int(cap * self.BUDGET_STRETCH_RATIO)
        filtered_stretch = [
            product
            for product in products
            if self._hard_filter(product, query, budget_max_rub=stretch_cap)
        ]
        stretch_results = [
            self._score(
                product,
                query,
                strict_budget_cap=cap,
                is_budget_stretch=product.price > cap if cap else False,
            )
            for product in filtered_stretch
        ]
        priced_stretch = [item for item in stretch_results if item.product.price > 0]
        if priced_stretch:
            stretch_results = priced_stretch
        stretch_results.sort(
            key=lambda item: (
                item.product.price <= cap,
                -item.fit_score,
                item.product.price,
            )
        )
        return stretch_results[:limit]

    def recommend(
        self, products: list[Product], query: RecommendationQuery, limit: int = 3
    ) -> list[Product]:
        return [
            item.product
            for item in self.recommend_scored(products=products, query=query, limit=limit)
        ]
