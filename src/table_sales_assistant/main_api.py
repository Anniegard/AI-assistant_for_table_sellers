import logging

import uvicorn

from table_sales_assistant.api.app import create_app
from table_sales_assistant.config import get_settings
from table_sales_assistant.logging_config import setup_logging


def main() -> None:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    if not settings.ENABLE_WEB_API:
        logger.info("Web API transport is disabled by ENABLE_WEB_API=false.")
        return
    uvicorn.run(create_app(settings), host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
