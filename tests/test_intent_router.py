from table_sales_assistant.assistant.intent_router import IntentRouter
from table_sales_assistant.assistant.models import DialogueIntent


def test_intent_router_detects_recommend() -> None:
    router = IntentRouter()
    assert router.route("Мне нужен стол для дома, рост 185") == DialogueIntent.RECOMMEND


def test_intent_router_detects_lead() -> None:
    router = IntentRouter()
    assert router.route("Можно оставить заявку?") == DialogueIntent.LEAVE_LEAD


def test_intent_router_detects_faq_delivery() -> None:
    router = IntentRouter()
    assert (
        router.route("Как с доставкой и гарантией?")
        == DialogueIntent.DELIVERY_WARRANTY_MATERIALS
    )
