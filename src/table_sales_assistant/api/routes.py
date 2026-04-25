import logging
from time import monotonic

from aiogram import Bot
from fastapi import APIRouter, HTTPException, status

from table_sales_assistant.api.schemas import (
    CreateSessionResponse,
    HealthResponse,
    LeadRequest,
    LeadResponse,
    LeadState,
    MessageRequest,
    MessageResponse,
    ProductCard,
)
from table_sales_assistant.api.session_store import InMemoryWebSessionStore
from table_sales_assistant.app_factory import AppServices
from table_sales_assistant.audit.service import detect_mode
from table_sales_assistant.config import Settings
from table_sales_assistant.notifications.formatters import build_manager_handoff_summary

logger = logging.getLogger(__name__)


def _quick_replies(cta: str | None, *, has_recommendations: bool) -> list[str]:
    replies: list[str] = []
    if cta:
        replies.append(cta)
    if has_recommendations:
        replies.append("Оставить заявку")
    if "Позвать менеджера" not in replies:
        replies.append("Позвать менеджера")
    return replies


def create_demo_router(
    services: AppServices,
    session_store: InMemoryWebSessionStore,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/api/demo", tags=["demo"])

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    @router.post(
        "/sessions",
        response_model=CreateSessionResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_session() -> CreateSessionResponse:
        session = session_store.create()
        return CreateSessionResponse(session_id=session.session_id)

    @router.post("/messages", response_model=MessageResponse)
    def send_message(payload: MessageRequest) -> MessageResponse:
        session = session_store.get(payload.session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        started = monotonic()
        services.explanation_service.reset_usage_tracking()
        services.audit_service.log_event(
            services.audit_service.create_event(
                event_type="user_message_received",
                conversation_id=session.session_id,
                channel="web_api",
                mode="unknown",
                status="success",
                user_message=payload.text,
                prompt_version="v1",
            )
        )
        try:
            response = services.dialogue_service.handle(payload.text, session.context)
            summary = session.context.get_context_summary()
            session.last_recommendation_context = summary
            products = services.recommendation_service.get_products_by_ids(
                session.context.recommended_products
            )
            product_cards = [
                ProductCard(
                    id=item.id,
                    name=item.name,
                    price=item.price,
                    product_url=item.product_url,
                )
                for item in products
            ]
            manager_summary = (
                summary["recent_dialogue_summary"] if response.start_lead_flow else None
            )
            mode = detect_mode(
                provider="openai",
                used_llm=services.explanation_service.last_response_used_llm,
            )
            services.audit_service.log_event(
                services.audit_service.create_event(
                    event_type="assistant_response_sent",
                    conversation_id=session.session_id,
                    channel="web_api",
                    mode=mode,
                    provider="openai" if mode == "openai" else None,
                    model=(
                        services.explanation_service.ai_client.model
                        if mode == "openai"
                        else None
                    ),
                    intent=response.intent.value,
                    status="success",
                    user_message=payload.text,
                    assistant_response=response.text,
                    latency_ms=int((monotonic() - started) * 1000),
                    recommended_products=list(session.context.recommended_products),
                    prompt_version="v1",
                    extra={"goal": response.goal.value},
                )
            )
            return MessageResponse(
                session_id=session.session_id,
                assistant_text=response.text,
                intent=response.intent.value,
                quick_replies=_quick_replies(
                    response.cta, has_recommendations=bool(session.context.recommended_products)
                ),
                recommended_products=product_cards,
                lead_state=LeadState(
                    start_lead_flow=response.start_lead_flow,
                    has_recommendations=bool(session.context.recommended_products),
                    known_params=summary["known_params"],
                ),
                manager_summary=manager_summary,
            )
        except HTTPException:
            raise
        except Exception:
            logger.exception(
                "Unhandled error in /api/demo/messages for session_id=%s",
                payload.session_id,
            )
            summary = session.context.get_context_summary()
            fallback_text = (
                "Сейчас есть технические ограничения внешнего AI-сервиса. "
                "Я продолжаю работать в демо-режиме: напишите рост и бюджет, "
                "и я подберу варианты из каталога."
            )
            services.audit_service.log_event(
                services.audit_service.create_event(
                    event_type="assistant_response_sent",
                    conversation_id=session.session_id,
                    channel="web_api",
                    mode=detect_mode(used_llm=services.explanation_service.last_response_used_llm),
                    status="error",
                    user_message=payload.text,
                    assistant_response=fallback_text,
                    error_type="message_processing_error",
                    error_message="Unhandled error in /api/demo/messages",
                    latency_ms=int((monotonic() - started) * 1000),
                    recommended_products=list(session.context.recommended_products),
                    prompt_version="v1",
                )
            )
            return MessageResponse(
                session_id=session.session_id,
                assistant_text=fallback_text,
                intent="fallback",
                quick_replies=["Подобрать стол", "Позвать менеджера"],
                recommended_products=[],
                lead_state=LeadState(
                    start_lead_flow=False,
                    has_recommendations=bool(session.context.recommended_products),
                    known_params=summary["known_params"],
                ),
                manager_summary=None,
            )

    @router.post("/leads", response_model=LeadResponse)
    async def create_lead(payload: LeadRequest) -> LeadResponse:
        session = session_store.get(payload.session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        context_summary = session.context.get_context_summary()
        lead_data = payload.model_dump()
        lead_data.update(
            known_params=context_summary["known_params"],
            recommended_products=list(session.context.recommended_products),
            recent_dialogue_summary=context_summary["recent_dialogue_summary"],
            recent_questions=context_summary["recent_questions"],
            selected_product_id=(
                session.context.recommended_products[0]
                if session.context.recommended_products
                else None
            ),
            assistant_comment=(
                "Клиент перешел в web API demo после консультации. "
                "Проверьте приоритеты по цене/стабильности."
            ),
        )
        lead = services.lead_service.build_lead(lead_data, source="web_demo")
        services.lead_repository.save(lead)
        if services.manager_notifier.manager_chat_id and settings.TELEGRAM_BOT_TOKEN.strip():
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            try:
                await services.manager_notifier.notify(bot, lead)
            finally:
                await bot.session.close()
        return LeadResponse(
            lead_id=lead.id,
            source=lead.source,
            manager_summary=build_manager_handoff_summary(lead),
        )

    return router
