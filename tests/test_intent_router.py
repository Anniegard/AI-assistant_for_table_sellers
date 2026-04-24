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


def test_intent_router_prioritizes_faq_motors() -> None:
    router = IntentRouter()
    assert router.route("А чем два мотора лучше?") == DialogueIntent.FAQ


def test_intent_router_detects_extended_lead_request() -> None:
    router = IntentRouter()
    assert router.route("Передай менеджеру, хочу заявку") == DialogueIntent.LEAVE_LEAD


def test_intent_router_detects_compare_phrases() -> None:
    router = IntentRouter()
    assert router.route("какой лучше") == DialogueIntent.COMPARE
    assert router.route("чем отличаются варианты") == DialogueIntent.COMPARE
