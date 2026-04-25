from dataclasses import dataclass

from table_sales_assistant.ai.client import OpenAIClient
from table_sales_assistant.assistant.dialogue_service import DialogueService
from table_sales_assistant.catalog.recommender import ProductRecommender
from table_sales_assistant.catalog.repository import ProductRepository
from table_sales_assistant.catalog.sqlite_repository import SQLiteCatalogRepository
from table_sales_assistant.config import Settings, get_settings
from table_sales_assistant.leads.repository import JSONLeadRepository
from table_sales_assistant.notifications.telegram_notifier import TelegramManagerNotifier
from table_sales_assistant.services.explanation_service import ExplanationService
from table_sales_assistant.services.faq_service import FAQService
from table_sales_assistant.services.lead_service import LeadService
from table_sales_assistant.services.recommendation_service import RecommendationService


@dataclass(slots=True)
class AppServices:
    recommendation_service: RecommendationService
    faq_service: FAQService
    explanation_service: ExplanationService
    dialogue_service: DialogueService
    lead_repository: JSONLeadRepository
    lead_service: LeadService
    manager_notifier: TelegramManagerNotifier


def _build_catalog_repository(settings: Settings) -> ProductRepository | SQLiteCatalogRepository:
    if settings.catalog_backend == "sqlite":
        if not settings.catalog_db_path.exists():
            raise FileNotFoundError(
                f"CATALOG_BACKEND=sqlite but DB does not exist: {settings.catalog_db_path}"
            )
        return SQLiteCatalogRepository(settings.catalog_db_path)
    return ProductRepository(settings.products_path)


def _build_faq_service(settings: Settings) -> FAQService:
    if settings.knowledge_backend == "sqlite":
        if not settings.knowledge_db_path.exists():
            raise FileNotFoundError(
                f"KNOWLEDGE_BACKEND=sqlite but DB does not exist: {settings.knowledge_db_path}"
            )
        return FAQService(sqlite_db_path=settings.knowledge_db_path)
    return FAQService(settings.knowledge_dir)


def build_app_services(settings: Settings | None = None) -> AppServices:
    app_settings = settings or get_settings()
    recommendation_service = RecommendationService(
        repository=_build_catalog_repository(app_settings),
        recommender=ProductRecommender(),
    )
    faq_service = _build_faq_service(app_settings)
    explanation_service = ExplanationService(OpenAIClient(app_settings.OPENAI_API_KEY))
    dialogue_service = DialogueService(
        recommendation_service=recommendation_service,
        faq_service=faq_service,
        explanation_service=explanation_service,
    )
    return AppServices(
        recommendation_service=recommendation_service,
        faq_service=faq_service,
        explanation_service=explanation_service,
        dialogue_service=dialogue_service,
        lead_repository=JSONLeadRepository(app_settings.leads_path),
        lead_service=LeadService(),
        manager_notifier=TelegramManagerNotifier(app_settings.MANAGER_TELEGRAM_CHAT_ID),
    )
