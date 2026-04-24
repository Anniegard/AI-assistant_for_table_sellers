from pathlib import Path

from table_sales_assistant.services.faq_service import FAQService


def test_faq_service_returns_answer_for_known_question() -> None:
    service = FAQService(Path("data/knowledge"))
    answer = service.answer("мотор")
    assert answer


def test_faq_service_returns_none_for_unknown_question() -> None:
    service = FAQService(Path("data/knowledge"))
    answer = service.answer("неизвестный_термин_12345")
    assert answer is None
