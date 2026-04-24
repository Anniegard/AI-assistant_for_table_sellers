from pathlib import Path

from table_sales_assistant.services.faq_service import FAQService
from table_sales_assistant.storage.sqlite import connect_sqlite, ensure_sqlite_schema


def test_faq_service_returns_answer_for_known_question() -> None:
    service = FAQService(Path("data/knowledge"))
    answer = service.answer("мотор")
    assert answer


def test_faq_service_finds_articles_by_russian_keywords() -> None:
    service = FAQService(Path("data/knowledge"))
    assert service.answer("два монитора")
    assert service.answer("доставка")
    assert service.answer("гарантия")
    assert service.answer("материал")


def test_faq_service_returns_none_for_unknown_question() -> None:
    service = FAQService(Path("data/knowledge"))
    answer = service.answer("неизвестный_термин_12345")
    assert answer is None


def test_faq_service_fallback_for_motor_question(tmp_path: Path) -> None:
    db_path = tmp_path / "empty_knowledge.sqlite"
    with connect_sqlite(db_path) as connection:
        ensure_sqlite_schema(
            connection, Path("src/table_sales_assistant/storage/sqlite_schema.sql")
        )
    service = FAQService(sqlite_db_path=db_path)
    answer = service.answer("чем два мотора лучше")
    assert answer
    assert "мотор" in answer.lower()
