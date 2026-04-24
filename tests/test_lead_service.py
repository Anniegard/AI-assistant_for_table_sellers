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
            "known_params": {"height_cm": 170, "budget_max": 65000},
            "recommended_products": ["demo-desk-003"],
            "recent_dialogue_summary": "Клиенту показали 2 варианта для дома.",
            "comment": "-",
        }
    )
    assert lead.name == "Анна"
    assert lead.source == "telegram_demo"
    assert lead.known_params["budget_max"] == 65000
    assert lead.recent_dialogue_summary


def test_build_lead_keeps_recommended_products_after_recommendation() -> None:
    lead = LeadService.build_lead(
        {
            "name": "Игорь",
            "phone": "+79005550000",
            "city": "Москва",
            "budget": 90000,
            "height_cm": 185,
            "use_case": "it_work",
            "monitors_count": 2,
            "recommended_products": ["desk-001", "desk-002", "desk-003"],
            "comment": "Хочу оформить быстро",
        }
    )
    assert lead.recommended_products == ["desk-001", "desk-002", "desk-003"]
