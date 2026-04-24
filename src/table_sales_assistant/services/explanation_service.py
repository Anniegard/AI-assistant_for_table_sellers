from table_sales_assistant.ai.client import OpenAIClient
from table_sales_assistant.ai.prompts import (
    RECOMMENDATION_EXPLANATION_PROMPT,
    SALES_CONSULTANT_SYSTEM_PROMPT,
)
from table_sales_assistant.catalog.models import Product


class ExplanationService:
    def __init__(self, ai_client: OpenAIClient) -> None:
        self.ai_client = ai_client

    def deterministic_explanation(self, product: Product) -> str:
        return (
            f"{product.name}: цена {product.price} руб, моторов {product.motors_count}, "
            f"столешница {product.tabletop_width_cm}x{product.tabletop_depth_cm} см, "
            f"грузоподъемность {product.lifting_capacity_kg} кг."
        )

    def explain_products(
        self,
        products: list[Product],
        query_context: dict[str, object],
    ) -> dict[str, str]:
        explanations: dict[str, str] = {}
        for product in products:
            fallback = self.deterministic_explanation(product)
            if not self.ai_client.is_enabled:
                explanations[product.id] = fallback
                continue
            try:
                user_prompt = (
                    f"Контекст запроса: {query_context}\n"
                    f"Товар: {product.model_dump()}\n"
                    "Объясни, почему этот вариант подходит. Не выдумывай новые товары."
                )
                ai_text = self.ai_client.simple_chat(
                    system_prompt=f"{SALES_CONSULTANT_SYSTEM_PROMPT}\n{RECOMMENDATION_EXPLANATION_PROMPT}",
                    user_prompt=user_prompt,
                )
                explanations[product.id] = ai_text or fallback
            except Exception:
                explanations[product.id] = fallback
        return explanations
