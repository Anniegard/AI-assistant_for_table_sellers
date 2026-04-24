from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ""
    OPENAI_API_KEY: str = ""
    MANAGER_TELEGRAM_CHAT_ID: str = ""
    PRODUCTS_PATH: str = "data/products.sample.json"
    KNOWLEDGE_DIR: str = "data/knowledge"
    LEADS_PATH: str = "data/leads.local.json"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def products_path(self) -> Path:
        return Path(self.PRODUCTS_PATH)

    @property
    def knowledge_dir(self) -> Path:
        return Path(self.KNOWLEDGE_DIR)

    @property
    def leads_path(self) -> Path:
        return Path(self.LEADS_PATH)


@lru_cache
def get_settings() -> Settings:
    return Settings()
