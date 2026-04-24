import logging

from aiogram import Bot

from table_sales_assistant.leads.models import Lead
from table_sales_assistant.notifications.formatters import format_lead_for_manager


class TelegramManagerNotifier:
    def __init__(self, manager_chat_id: str) -> None:
        self.manager_chat_id = manager_chat_id.strip()
        self.logger = logging.getLogger(__name__)

    async def notify(self, bot: Bot, lead: Lead) -> bool:
        if not self.manager_chat_id:
            self.logger.info("MANAGER_TELEGRAM_CHAT_ID is empty. Manager notification skipped.")
            return False
        await bot.send_message(chat_id=self.manager_chat_id, text=format_lead_for_manager(lead))
        return True
