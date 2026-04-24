from pathlib import Path

from table_sales_assistant.ingest.stolstoya_importer import (
    _parse_knowledge,
    _parse_product,
    _print_report,
)


def _read_fixture(name: str) -> str:
    return Path("tests/fixtures", name).read_text(encoding="utf-8")


def test_parse_product_from_catalog_fixture() -> None:
    html = _read_fixture("stolstoya_catalog_sample.html")
    product = _parse_product("https://stolstoya.ru/catalog/aksessuary/cable-tray", html)
    assert product["price_rub"] == 3490
    assert product["lifting_capacity_kg"] == 250
    assert product["category"] == "accessory"


def test_parse_knowledge_from_faq_fixture() -> None:
    html = _read_fixture("stolstoya_faq_sample.html")
    doc = _parse_knowledge("https://stolstoya.ru/faq/motors", html)
    assert doc["doc_type"] == "faq"
    assert "два мотора" in str(doc["content"]).lower()


def test_import_report_contains_duplicate_source_warning(capsys) -> None:
    products = [
        {
            "id": "p1",
            "category": "adjustable_desk",
            "source_url": "https://example.local/p",
            "price_rub": None,
            "min_height_cm": None,
            "max_height_cm": None,
        },
        {
            "id": "p2",
            "category": "unknown",
            "source_url": "https://example.local/p",
            "price_rub": 1000,
            "min_height_cm": None,
            "max_height_cm": None,
        },
    ]
    _print_report(products, [])
    output = capsys.readouterr().out.lower()
    assert "duplicate source_url" in output
    assert "unknown products" in output
