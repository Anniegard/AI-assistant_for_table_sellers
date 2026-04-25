from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENABLE_TELEGRAM: bool = True
    ENABLE_WEB_API: bool = False
    TELEGRAM_BOT_TOKEN: str = ""
    OPENAI_API_KEY: str = ""
    MANAGER_TELEGRAM_CHAT_ID: str = ""
    WEB_ALLOWED_ORIGINS: str = "*"
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 8000
    PRODUCTS_PATH: str = "data/products.sample.json"
    KNOWLEDGE_DIR: str = "data/knowledge"
    LEADS_PATH: str = "data/leads.local.json"
    LOG_LEVEL: str = "INFO"
    CATALOG_BACKEND: str = "json"
    CATALOG_DB_PATH: str = "data/private/stolstoya_demo.sqlite"
    KNOWLEDGE_BACKEND: str = "markdown"
    KNOWLEDGE_DB_PATH: str = "data/private/stolstoya_demo.sqlite"

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

    @property
    def catalog_backend(self) -> str:
        return self.CATALOG_BACKEND.strip().lower()

    @property
    def catalog_db_path(self) -> Path:
        return Path(self.CATALOG_DB_PATH)

    @property
    def knowledge_backend(self) -> str:
        return self.KNOWLEDGE_BACKEND.strip().lower()

    @property
    def knowledge_db_path(self) -> Path:
        return Path(self.KNOWLEDGE_DB_PATH)

    @property
    def web_allowed_origins(self) -> list[str]:
        raw = self.WEB_ALLOWED_ORIGINS.strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
