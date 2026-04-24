from table_sales_assistant.services.lead_service import LeadService


def test_parse_bool_understands_russian_yes() -> None:
    assert LeadService.parse_bool("да") is True
    assert LeadService.parse_bool("нет") is False


def test_build_lead_contains_required_fields() -> None:
    lead = LeadService.build_lead(
        {
            "name": "Анна",
            "phone": "+79001112233",
            "city": "Казань",
            "height_cm": 170,
            "budget": 65000,
            "use_case": "it_work",
            "monitors_count": 2,
            "has_pc_case": False,
            "preferred_size": "120x70",
            "needs_delivery": True,
            "needs_assembly": True,
            "recommended_products": ["demo-desk-003"],
            "comment": "-",
        }
    )
    assert lead.name == "Анна"
    assert lead.source == "telegram_demo"
