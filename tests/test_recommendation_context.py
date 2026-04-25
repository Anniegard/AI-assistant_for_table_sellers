from table_sales_assistant.bot.handlers import _build_recommendation_context, _map_use_case


def test_use_case_mapping_uses_human_labels() -> None:
    assert _map_use_case("Для дома") == "home_office"
    assert _map_use_case("Для IT / разработки") == "gaming"
    assert _map_use_case("Не знаю, помогите выбрать") is None


def test_build_recommendation_context_preserves_products_and_params() -> None:
    context = _build_recommendation_context(
        {
            "budget": 80000,
            "user_height": 182,
            "monitors_count": 2,
            "use_case": "it_work",
            "recommended_products": ["demo-desk-003", "demo-desk-004"],
            "ignored_field": "x",
        }
    )
    assert context["budget"] == 80000
    assert context["height_cm"] == 182
    assert context["recommended_products"] == ["demo-desk-003", "demo-desk-004"]
