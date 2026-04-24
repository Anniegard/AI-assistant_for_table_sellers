from table_sales_assistant.assistant.models import DialogueContext, KnownClientParams
from table_sales_assistant.bot.handlers import (
    _reset_user_context,
    dialogue_context_store,
    last_recommendation_context,
)


def test_lead_context_after_recommendation_keeps_core_fields() -> None:
    context = DialogueContext(user_id=42, known_params=KnownClientParams())
    context.known_params.budget_max = 70000
    context.known_params.height_cm = 185
    context.known_params.monitors_count = 2
    context.recommended_products = ["demo-desk-004", "demo-desk-011"]
    assert context.known_params.budget_max == 70000
    assert context.recommended_products[0] == "demo-desk-004"


def test_reset_user_context_clears_known_params_and_history() -> None:
    user_id = 777
    context = DialogueContext(user_id=user_id, known_params=KnownClientParams(height_cm=190))
    context.add_user_message("рост 190")
    dialogue_context_store[user_id] = context
    last_recommendation_context[user_id] = {"budget": 50000}

    _reset_user_context(user_id)

    assert user_id not in dialogue_context_store
    assert user_id not in last_recommendation_context
