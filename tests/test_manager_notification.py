import asyncio

from table_sales_assistant.notifications.telegram_notifier import TelegramManagerNotifier
from table_sales_assistant.services.lead_service import LeadService


class DummyBot:
    def __init__(self) -> None:
        self.calls = []

    async def send_message(self, chat_id: str, text: str) -> None:
        self.calls.append((chat_id, text))


def _sample_lead():
    return LeadService.build_lead(
        {
            "name": "Олег",
            "phone": "+79990000000",
            "city": "СПб",
            "height_cm": 180,
            "budget": 70000,
            "use_case": "home_office",
            "monitors_count": 2,
            "has_pc_case": True,
            "preferred_size": "140x80",
            "needs_delivery": True,
            "needs_assembly": False,
            "recommended_products": ["demo-desk-011"],
            "comment": "Тест",
        }
    )


def test_manager_notification_skips_when_chat_id_empty() -> None:
    notifier = TelegramManagerNotifier("")
    bot = DummyBot()
    sent = asyncio.run(notifier.notify(bot, _sample_lead()))
    assert sent is False
    assert bot.calls == []


def test_manager_notification_sends_when_chat_id_set() -> None:
    notifier = TelegramManagerNotifier("12345")
    bot = DummyBot()
    sent = asyncio.run(notifier.notify(bot, _sample_lead()))
    assert sent is True
    assert bot.calls
    _, text = bot.calls[0]
    assert "Имя: Олег" in text
    assert "Телефон: +79990000000" in text
    assert "Город: СПб" in text
    assert "Бюджет: 70000" in text
    assert "Рост: 180" in text
    assert "Сценарий: home_office" in text
    assert "Мониторы: 2" in text
    assert "Рекомендации: demo-desk-011" in text
    assert "Комментарий: Тест" in text
    assert "Сводка для менеджера:" in text
