from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from table_sales_assistant.api.routes import create_demo_router
from table_sales_assistant.api.session_store import InMemoryWebSessionStore
from table_sales_assistant.app_factory import AppServices, build_app_services
from table_sales_assistant.config import Settings, get_settings


def create_app(
    settings: Settings | None = None,
    services: AppServices | None = None,
    session_store: InMemoryWebSessionStore | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    app_services = services or build_app_services(app_settings)
    store = session_store or InMemoryWebSessionStore()

    app = FastAPI(title="Table Sales Assistant Demo API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.web_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(create_demo_router(app_services, store, app_settings))
    return app
