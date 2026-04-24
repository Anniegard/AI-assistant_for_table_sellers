from table_sales_assistant.assistant.models import DialogueContext, KnownClientParams


def test_lead_context_after_recommendation_keeps_core_fields() -> None:
    context = DialogueContext(user_id=42, known_params=KnownClientParams())
    context.known_params.budget_max = 70000
    context.known_params.height_cm = 185
    context.known_params.monitors_count = 2
    context.recommended_products = ["demo-desk-004", "demo-desk-011"]
    assert context.known_params.budget_max == 70000
    assert context.recommended_products[0] == "demo-desk-004"
