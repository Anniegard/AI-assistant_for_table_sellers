from pathlib import Path

from table_sales_assistant.services.faq_service import FAQService


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
