from table_sales_assistant.notifications.formatters import format_lead_for_manager
from table_sales_assistant.services.lead_service import LeadService


def test_manager_handoff_summary_contains_extended_context() -> None:
    lead = LeadService.build_lead(
        {
            "name": "Мария",
            "phone": "+79990000000",
            "city": "Москва",
            "height_cm": 182,
            "budget": 80000,
            "use_case": "it_work",
            "monitors_count": 2,
            "has_pc_case": True,
            "needs_assembly": True,
            "recommended_products": ["demo-desk-004", "demo-desk-011"],
            "recent_questions": ["Почему два мотора?", "Есть дешевле?"],
            "selected_product_id": "demo-desk-004",
            "assistant_comment": "Важно уточнить фактическую нагрузку и глубину столешницы.",
            "comment": "Связаться после 19:00",
        }
    )
    formatted = format_lead_for_manager(lead)
    assert "Вопросы клиента:" in formatted
    assert "Выбранный вариант: demo-desk-004" in formatted
    assert "Комментарий ассистента:" in formatted
