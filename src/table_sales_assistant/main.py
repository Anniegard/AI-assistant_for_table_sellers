import logging

from table_sales_assistant.config import get_settings
from table_sales_assistant.logging_config import setup_logging


def main() -> None:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("Table sales assistant foundation is ready.")
    logger.info("TODO: initialize aiogram app and run polling.")


if __name__ == "__main__":
    main()
