import json

from table_sales_assistant.leads.repository import JSONLeadRepository
from table_sales_assistant.services.lead_service import LeadService


def test_json_lead_repository_saves_lead(tmp_path) -> None:
    repository = JSONLeadRepository(tmp_path / "leads.local.json")
    lead = LeadService.build_lead(
        {
            "name": "Иван",
            "phone": "+79000000000",
            "city": "Москва",
            "height_cm": 178,
            "budget": 50000,
            "use_case": "home_office",
            "monitors_count": 2,
            "has_pc_case": True,
            "preferred_size": "140x70",
            "needs_delivery": True,
            "needs_assembly": False,
            "recommended_products": ["demo-desk-004"],
            "comment": "Тест",
        }
    )

    repository.save(lead)

    raw = json.loads((tmp_path / "leads.local.json").read_text(encoding="utf-8"))
    assert len(raw) == 1
    assert raw[0]["name"] == "Иван"
