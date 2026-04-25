from types import SimpleNamespace

import pytest

from table_sales_assistant.bot import handlers
from table_sales_assistant.bot.handlers import (
    faq_answer,
    recommendation_monitors,
    recommendation_use_case,
)
from table_sales_assistant.bot.messages import (
    ASK_MONITORS_TEXT,
    ASK_USE_CASE_TEXT,
    FAQ_NO_HITS_TEXT,
    NO_PRODUCTS_TEXT,
)
from table_sales_assistant.bot.states import RecommendationStates
from table_sales_assistant.catalog.models import Product


class DummyState:
    def __init__(self, data: dict[str, object] | None = None) -> None:
        self.data = dict(data or {})
        self.state = None

    async def set_state(self, value: object) -> None:
        self.state = value

    async def update_data(self, **kwargs: object) -> None:
        self.data.update(kwargs)

    async def get_data(self) -> dict[str, object]:
        return dict(self.data)

    async def clear(self) -> None:
        self.data.clear()
        self.state = None

    async def get_state(self) -> object:
        return self.state


class DummyMessage:
    def __init__(self, text: str, user_id: int = 101) -> None:
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.bot = SimpleNamespace(id=1)
        self.answers: list[dict[str, object]] = []

    async def answer(self, text: str, reply_markup: object | None = None) -> None:
        self.answers.append({"text": text, "reply_markup": reply_markup})


class StubRecommendationService:
    def __init__(self, products: list[Product]) -> None:
        self.products = products
        self.last_query = None

    def get_recommendations(self, query):  # noqa: ANN001
        self.last_query = query
        return list(self.products)


class StubExplanationService:
    def explain_products(self, products, query_context):  # noqa: ANN001
        return {product.id: "Подходит под задачу." for product in products}


class StubFAQService:
    def __init__(self, response: str | None) -> None:
        self.response = response

    def answer(self, question: str) -> str | None:  # noqa: ARG002
        return self.response


def _demo_product(product_id: str = "demo-desk-1") -> Product:
    return Product(
        id=product_id,
        name="Demo Desk",
        category="adjustable_desk",
        segment="demo",
        price=65000,
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
        product_url="https://example.com/demo-desk",
        in_stock=True,
        short_description="demo",
    )


@pytest.mark.anyio
async def test_guided_recommendation_without_use_case(monkeypatch: pytest.MonkeyPatch) -> None:
    handlers.last_recommendation_context.clear()
    service = StubRecommendationService(products=[_demo_product()])
    monkeypatch.setattr(handlers, "recommendation_service", service)
    monkeypatch.setattr(handlers, "explanation_service", StubExplanationService())

    state = DummyState(data={"budget": 70000, "user_height": 180})
    monitors_message = DummyMessage("2")
    await recommendation_monitors(monitors_message, state)

    assert state.state == RecommendationStates.use_case
    assert monitors_message.answers[-1]["text"] == ASK_USE_CASE_TEXT

    use_case_message = DummyMessage("Пропустить")
    await recommendation_use_case(use_case_message, state)

    assert service.last_query is not None
    assert service.last_query.use_case is None
    assert any("Рекомендации готовы" in item["text"] for item in use_case_message.answers)


@pytest.mark.anyio
async def test_guided_recommendation_with_use_case(monkeypatch: pytest.MonkeyPatch) -> None:
    handlers.last_recommendation_context.clear()
    service = StubRecommendationService(products=[_demo_product()])
    monkeypatch.setattr(handlers, "recommendation_service", service)
    monkeypatch.setattr(handlers, "explanation_service", StubExplanationService())

    state = DummyState(data={"budget": 70000, "user_height": 180})
    await recommendation_monitors(DummyMessage("2"), state)
    await recommendation_use_case(DummyMessage("Для дома"), state)

    assert service.last_query is not None
    assert service.last_query.use_case == "home_office"


@pytest.mark.anyio
async def test_guided_recommendation_invalid_monitors(monkeypatch: pytest.MonkeyPatch) -> None:
    service = StubRecommendationService(products=[_demo_product()])
    monkeypatch.setattr(handlers, "recommendation_service", service)
    monkeypatch.setattr(handlers, "explanation_service", StubExplanationService())

    state = DummyState(data={"budget": 70000, "user_height": 180})
    message = DummyMessage("два")
    await recommendation_monitors(message, state)

    assert message.answers[-1]["text"] == ASK_MONITORS_TEXT
    assert state.state is None


@pytest.mark.anyio
async def test_guided_recommendation_no_products_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    handlers.last_recommendation_context.clear()
    service = StubRecommendationService(products=[])
    monkeypatch.setattr(handlers, "recommendation_service", service)
    monkeypatch.setattr(handlers, "explanation_service", StubExplanationService())

    state = DummyState(data={"budget": 35000, "user_height": 180})
    await recommendation_monitors(DummyMessage("2"), state)
    use_case_message = DummyMessage("Пропустить")
    await recommendation_use_case(use_case_message, state)

    assert use_case_message.answers[-1]["text"] == NO_PRODUCTS_TEXT


@pytest.mark.anyio
async def test_faq_no_hit_fallback_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(handlers, "faq_service", StubFAQService(response=None))
    state = DummyState()
    message = DummyMessage("Какой ресурс моторов?")

    await faq_answer(message, state)

    assert message.answers[-1]["text"] == FAQ_NO_HITS_TEXT
