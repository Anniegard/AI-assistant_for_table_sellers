from collections.abc import Mapping

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from table_sales_assistant.ai.client import OpenAIClient
from table_sales_assistant.assistant.dialogue_service import DialogueService
from table_sales_assistant.assistant.models import DialogueContext, KnownClientParams
from table_sales_assistant.bot.keyboards import main_menu_keyboard, recommendation_ready_keyboard
from table_sales_assistant.bot.messages import (
    ASK_BUDGET_TEXT,
    ASK_HEIGHT_TEXT,
    ASK_MONITORS_TEXT,
    ASK_USE_CASE_TEXT,
    ASSISTANT_RESET_TEXT,
    DEMO_MODE_TEXT,
    FAQ_NO_HITS_TEXT,
    FAQ_PROMPT_TEXT,
    GENERIC_ERROR_TEXT,
    LEAD_ASK_ASSEMBLY_TEXT,
    LEAD_ASK_BUDGET_TEXT,
    LEAD_ASK_CITY_TEXT,
    LEAD_ASK_COMMENT_TEXT,
    LEAD_ASK_DELIVERY_TEXT,
    LEAD_ASK_HAS_PC_CASE_TEXT,
    LEAD_ASK_HEIGHT_TEXT,
    LEAD_ASK_MONITORS_TEXT,
    LEAD_ASK_PHONE_TEXT,
    LEAD_ASK_SIZE_TEXT,
    LEAD_ASK_USE_CASE_TEXT,
    LEAD_SAVED_TEXT,
    LEAD_START_AFTER_RECOMMENDATION_TEXT,
    LEAD_START_TEXT,
    MENU_TEXT,
    NO_PRODUCTS_TEXT,
    WELCOME_TEXT,
)
from table_sales_assistant.bot.states import FAQStates, LeadCollectionStates, RecommendationStates
from table_sales_assistant.catalog.recommender import ProductRecommender, RecommendationQuery
from table_sales_assistant.catalog.repository import ProductRepository
from table_sales_assistant.catalog.sqlite_repository import SQLiteCatalogRepository
from table_sales_assistant.config import get_settings
from table_sales_assistant.leads.repository import JSONLeadRepository
from table_sales_assistant.notifications.telegram_notifier import TelegramManagerNotifier
from table_sales_assistant.observability import log_dialogue_event
from table_sales_assistant.services.explanation_service import ExplanationService
from table_sales_assistant.services.faq_service import FAQService
from table_sales_assistant.services.lead_service import LeadService
from table_sales_assistant.services.recommendation_service import RecommendationService

router = Router()
settings = get_settings()


def _build_catalog_repository():
    if settings.catalog_backend == "sqlite":
        if not settings.catalog_db_path.exists():
            raise FileNotFoundError(
                f"CATALOG_BACKEND=sqlite but DB does not exist: {settings.catalog_db_path}"
            )
        return SQLiteCatalogRepository(settings.catalog_db_path)
    return ProductRepository(settings.products_path)


def _build_faq_service() -> FAQService:
    if settings.knowledge_backend == "sqlite":
        if not settings.knowledge_db_path.exists():
            raise FileNotFoundError(
                f"KNOWLEDGE_BACKEND=sqlite but DB does not exist: {settings.knowledge_db_path}"
            )
        return FAQService(sqlite_db_path=settings.knowledge_db_path)
    return FAQService(settings.knowledge_dir)


recommendation_service = RecommendationService(
    repository=_build_catalog_repository(),
    recommender=ProductRecommender(),
)
faq_service = _build_faq_service()
explanation_service = ExplanationService(OpenAIClient(settings.OPENAI_API_KEY))
dialogue_service = DialogueService(
    recommendation_service=recommendation_service,
    faq_service=faq_service,
    explanation_service=explanation_service,
)
lead_repository = JSONLeadRepository(settings.leads_path)
lead_service = LeadService()
manager_notifier = TelegramManagerNotifier(settings.MANAGER_TELEGRAM_CHAT_ID)


USE_CASE_MAP = {
    "для дома": "home_office",
    "для офиса": "family_workspace",
    "для it / разработки": "it_work",
    "для работы с двумя мониторами": "engineering",
    "для руководителя": "executive_office",
    "для учебы": "study",
    "не знаю, помогите выбрать": None,
}

last_recommendation_context: dict[int, dict[str, object]] = {}
dialogue_context_store: dict[int, DialogueContext] = {}


def _reset_user_context(user_id: int) -> None:
    last_recommendation_context.pop(user_id, None)
    dialogue_context_store.pop(user_id, None)


def _user_id(message: Message) -> int | None:
    return message.from_user.id if message.from_user else None


def _bot_id(message: Message) -> int | None:
    return message.bot.id if message.bot else None


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _map_use_case(raw_value: str | None) -> str | None:
    normalized = _normalize_text(raw_value)
    if not normalized:
        return None
    if normalized == "пропустить":
        return None
    return USE_CASE_MAP.get(normalized)


def _build_recommendation_context(data: Mapping[str, object]) -> dict[str, object]:
    context: dict[str, object] = {}
    for field in (
        "budget",
        "user_height",
        "monitors_count",
        "use_case",
        "recommended_products",
        "known_params",
        "recent_dialogue_summary",
        "recent_questions",
        "assistant_comment",
    ):
        if field in data and data[field] is not None:
            context[field] = data[field]
    if "user_height" in context:
        context["height_cm"] = context["user_height"]
    return context


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    log_dialogue_event(
        phase="handler_enter",
        function_name="start_handler",
        user_id=_user_id(message),
        question=message.text,
        bot_id=_bot_id(message),
    )
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())
    log_dialogue_event(
        phase="bot_answer",
        function_name="start_handler",
        user_id=_user_id(message),
        answer=WELCOME_TEXT,
        bot_id=_bot_id(message),
    )
    await message.answer(MENU_TEXT)
    log_dialogue_event(
        phase="bot_answer",
        function_name="start_handler",
        user_id=_user_id(message),
        answer=MENU_TEXT,
        bot_id=_bot_id(message),
    )


@router.message(F.text == "Демо-режим")
async def demo_mode_info(message: Message) -> None:
    await message.answer(DEMO_MODE_TEXT, reply_markup=main_menu_keyboard())


@router.message(F.text == "Подобрать стол")
async def start_recommendation_flow(message: Message, state: FSMContext) -> None:
    await state.set_state(RecommendationStates.budget)
    await message.answer(ASK_BUDGET_TEXT)


@router.message(RecommendationStates.budget)
async def recommendation_budget(message: Message, state: FSMContext) -> None:
    try:
        budget = int((message.text or "").strip())
    except ValueError:
        await message.answer(ASK_BUDGET_TEXT)
        return
    await state.update_data(budget=budget)
    await state.set_state(RecommendationStates.user_height)
    await message.answer(ASK_HEIGHT_TEXT)


@router.message(RecommendationStates.user_height)
async def recommendation_height(message: Message, state: FSMContext) -> None:
    try:
        user_height = int((message.text or "").strip())
    except ValueError:
        await message.answer(ASK_HEIGHT_TEXT)
        return
    await state.update_data(user_height=user_height)
    await state.set_state(RecommendationStates.monitors_count)
    await message.answer(ASK_MONITORS_TEXT)


@router.message(RecommendationStates.monitors_count)
async def recommendation_monitors(message: Message, state: FSMContext) -> None:
    log_dialogue_event(
        phase="handler_enter",
        function_name="recommendation_monitors",
        user_id=_user_id(message),
        question=message.text,
        bot_id=_bot_id(message),
    )
    try:
        monitors_count = int((message.text or "").strip())
    except ValueError:
        await message.answer(ASK_MONITORS_TEXT)
        return
    await state.update_data(monitors_count=monitors_count)
    await state.set_state(RecommendationStates.use_case)
    await message.answer(ASK_USE_CASE_TEXT)


@router.message(RecommendationStates.use_case)
async def recommendation_use_case(message: Message, state: FSMContext) -> None:
    log_dialogue_event(
        phase="handler_enter",
        function_name="recommendation_use_case",
        user_id=_user_id(message),
        question=message.text,
        bot_id=_bot_id(message),
    )
    await state.update_data(use_case=_map_use_case(message.text))
    raw_data = await state.get_data()
    query = RecommendationQuery(
        budget=raw_data.get("budget"),
        user_height_cm=raw_data.get("user_height"),
        monitors_count=raw_data.get("monitors_count"),
        use_case=raw_data.get("use_case"),
        motors_preference=None,
    )
    products = recommendation_service.get_recommendations(query)
    if not products:
        await message.answer(NO_PRODUCTS_TEXT, reply_markup=main_menu_keyboard())
        log_dialogue_event(
            phase="bot_answer",
            function_name="recommendation_use_case",
            user_id=_user_id(message),
            answer=NO_PRODUCTS_TEXT,
            bot_id=_bot_id(message),
        )
        await state.clear()
        return

    explanations = explanation_service.explain_products(products, query_context=raw_data)
    for idx, product in enumerate(products, start=1):
        explanation = explanations.get(product.id, "")
        price_text = (
            f"{product.price} руб"
            if product.price > 0
            else "цена не указана в демо-базе"
        )
        await message.answer(
            f"{idx}. {product.name}\n"
            f"Цена: {price_text}\n"
            f"Моторов: {product.motors_count}\n"
            f"Размер: {product.tabletop_width_cm}x{product.tabletop_depth_cm} см\n"
            f"Ссылка: {product.product_url}\n"
            f"Комментарий: {explanation}"
        )
        log_dialogue_event(
            phase="bot_answer",
            function_name="recommendation_use_case",
            user_id=_user_id(message),
            answer=f"recommendation_item:{product.id}",
            bot_id=_bot_id(message),
        )
    await state.update_data(recommended_products=[p.id for p in products])
    updated_data = await state.get_data()
    if message.from_user:
        last_recommendation_context[message.from_user.id] = (
            _build_recommendation_context(updated_data)
        )
    await message.answer(
        "Рекомендации готовы. Можно оставить заявку по этим вариантам.",
        reply_markup=recommendation_ready_keyboard(),
    )
    log_dialogue_event(
        phase="bot_answer",
        function_name="recommendation_use_case",
        user_id=_user_id(message),
        answer="Рекомендации готовы. Можно оставить заявку по этим вариантам.",
        bot_id=_bot_id(message),
        extra={"recommended_products": [p.id for p in products]},
    )
    await state.clear()


@router.message(F.text == "Задать вопрос")
async def start_faq_flow(message: Message, state: FSMContext) -> None:
    await state.set_state(FAQStates.waiting_question)
    await message.answer(FAQ_PROMPT_TEXT)


@router.message(FAQStates.waiting_question)
async def faq_answer(message: Message, state: FSMContext) -> None:
    log_dialogue_event(
        phase="handler_enter",
        function_name="faq_answer",
        user_id=_user_id(message),
        question=message.text,
        bot_id=_bot_id(message),
    )
    answer = faq_service.answer((message.text or "").strip())
    await state.clear()
    if answer:
        await message.answer(answer, reply_markup=main_menu_keyboard())
        log_dialogue_event(
            phase="bot_answer",
            function_name="faq_answer",
            user_id=_user_id(message),
            answer=answer,
            bot_id=_bot_id(message),
        )
        return
    await message.answer(FAQ_NO_HITS_TEXT, reply_markup=main_menu_keyboard())
    log_dialogue_event(
        phase="bot_answer",
        function_name="faq_answer",
        user_id=_user_id(message),
        answer=FAQ_NO_HITS_TEXT,
        bot_id=_bot_id(message),
    )


@router.message(F.text == "Оставить заявку")
async def start_lead_flow(message: Message, state: FSMContext) -> None:
    user_context = (
        last_recommendation_context.get(message.from_user.id, {}) if message.from_user else {}
    )
    if user_context:
        await state.update_data(**user_context, lead_short_flow=True)
        await message.answer(LEAD_START_AFTER_RECOMMENDATION_TEXT)
    else:
        await message.answer(LEAD_START_TEXT)
    await state.set_state(LeadCollectionStates.name)


@router.message(F.text == "Оставить заявку по этим вариантам")
async def start_lead_flow_for_recommendation(message: Message, state: FSMContext) -> None:
    user_context = (
        last_recommendation_context.get(message.from_user.id, {}) if message.from_user else {}
    )
    if user_context:
        await state.update_data(**user_context, lead_short_flow=True)
        await message.answer(LEAD_START_AFTER_RECOMMENDATION_TEXT)
    else:
        await message.answer(LEAD_START_TEXT)
    await state.set_state(LeadCollectionStates.name)


@router.message(LeadCollectionStates.name)
async def lead_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=(message.text or "").strip())
    await state.set_state(LeadCollectionStates.phone)
    await message.answer(LEAD_ASK_PHONE_TEXT)


@router.message(LeadCollectionStates.phone)
async def lead_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=(message.text or "").strip())
    await state.set_state(LeadCollectionStates.city)
    await message.answer(LEAD_ASK_CITY_TEXT)


@router.message(LeadCollectionStates.city)
async def lead_city(message: Message, state: FSMContext) -> None:
    await state.update_data(city=(message.text or "").strip())
    data = await state.get_data()
    if data.get("lead_short_flow"):
        await state.set_state(LeadCollectionStates.comment)
        await message.answer(LEAD_ASK_COMMENT_TEXT)
        return
    await state.set_state(LeadCollectionStates.height_cm)
    await message.answer(LEAD_ASK_HEIGHT_TEXT)


@router.message(LeadCollectionStates.height_cm)
async def lead_height(message: Message, state: FSMContext) -> None:
    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer(LEAD_ASK_HEIGHT_TEXT)
        return
    await state.update_data(height_cm=value)
    await state.set_state(LeadCollectionStates.budget)
    await message.answer(LEAD_ASK_BUDGET_TEXT)


@router.message(LeadCollectionStates.budget)
async def lead_budget(message: Message, state: FSMContext) -> None:
    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer(LEAD_ASK_BUDGET_TEXT)
        return
    await state.update_data(budget=value)
    await state.set_state(LeadCollectionStates.use_case)
    await message.answer(LEAD_ASK_USE_CASE_TEXT)


@router.message(LeadCollectionStates.use_case)
async def lead_use_case(message: Message, state: FSMContext) -> None:
    await state.update_data(use_case=_map_use_case(message.text))
    await state.set_state(LeadCollectionStates.monitors_count)
    await message.answer(LEAD_ASK_MONITORS_TEXT)


@router.message(LeadCollectionStates.monitors_count)
async def lead_monitors(message: Message, state: FSMContext) -> None:
    try:
        value = int((message.text or "").strip())
    except ValueError:
        await message.answer(LEAD_ASK_MONITORS_TEXT)
        return
    await state.update_data(monitors_count=value)
    await state.set_state(LeadCollectionStates.has_pc_case)
    await message.answer(LEAD_ASK_HAS_PC_CASE_TEXT)


@router.message(LeadCollectionStates.has_pc_case)
async def lead_has_pc_case(message: Message, state: FSMContext) -> None:
    await state.update_data(has_pc_case=lead_service.parse_bool(message.text or ""))
    await state.set_state(LeadCollectionStates.preferred_size)
    await message.answer(LEAD_ASK_SIZE_TEXT)


@router.message(LeadCollectionStates.preferred_size)
async def lead_size(message: Message, state: FSMContext) -> None:
    await state.update_data(preferred_size=(message.text or "").strip())
    await state.set_state(LeadCollectionStates.needs_delivery)
    await message.answer(LEAD_ASK_DELIVERY_TEXT)


@router.message(LeadCollectionStates.needs_delivery)
async def lead_delivery(message: Message, state: FSMContext) -> None:
    await state.update_data(needs_delivery=lead_service.parse_bool(message.text or ""))
    await state.set_state(LeadCollectionStates.needs_assembly)
    await message.answer(LEAD_ASK_ASSEMBLY_TEXT)


@router.message(LeadCollectionStates.needs_assembly)
async def lead_assembly(message: Message, state: FSMContext) -> None:
    await state.update_data(needs_assembly=lead_service.parse_bool(message.text or ""))
    await state.set_state(LeadCollectionStates.comment)
    await message.answer(LEAD_ASK_COMMENT_TEXT)


@router.message(LeadCollectionStates.comment)
async def lead_comment(message: Message, state: FSMContext) -> None:
    log_dialogue_event(
        phase="handler_enter",
        function_name="lead_comment",
        user_id=_user_id(message),
        question=message.text,
        bot_id=_bot_id(message),
    )
    data = await state.get_data()
    data["comment"] = (message.text or "").strip()
    if message.from_user:
        context = dialogue_context_store.get(message.from_user.id)
        if context:
            summary = context.get_context_summary()
            data["recent_questions"] = context.recent_questions[-5:]
            data["known_params"] = summary["known_params"]
            data["recent_dialogue_summary"] = summary["recent_dialogue_summary"]
            data["selected_product_id"] = (
                context.recommended_products[0] if context.recommended_products else None
            )
            data["assistant_comment"] = (
                "Пользователь прошел консультацию в боте. "
                "Проверьте финальные требования к сетапу, размеру и срокам поставки."
            )
    try:
        lead = lead_service.build_lead(data)
        lead_repository.save(lead)
        await manager_notifier.notify(message.bot, lead)
        await message.answer(LEAD_SAVED_TEXT, reply_markup=main_menu_keyboard())
        log_dialogue_event(
            phase="lead_saved",
            function_name="lead_comment",
            user_id=_user_id(message),
            answer=LEAD_SAVED_TEXT,
            lead_id=lead.id,
            bot_id=_bot_id(message),
        )
    except Exception:
        await message.answer(GENERIC_ERROR_TEXT, reply_markup=main_menu_keyboard())
        log_dialogue_event(
            phase="lead_save_error",
            function_name="lead_comment",
            user_id=_user_id(message),
            answer=GENERIC_ERROR_TEXT,
            bot_id=_bot_id(message),
        )
    finally:
        if message.from_user:
            _reset_user_context(message.from_user.id)
        await state.clear()


@router.message(F.text == "Начать заново")
async def restart_dialogue(message: Message, state: FSMContext) -> None:
    await state.clear()
    if message.from_user:
        _reset_user_context(message.from_user.id)
    await message.answer(ASSISTANT_RESET_TEXT, reply_markup=main_menu_keyboard())


@router.message(F.text == "Отмена")
async def cancel_dialogue(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Действие отменено. Могу продолжить подбор, сравнение или оформить заявку.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "Позвать менеджера")
async def handoff_to_manager(message: Message, state: FSMContext) -> None:
    await start_lead_flow(message, state)


@router.message(F.text == "Сравнить варианты")
async def compare_variants(message: Message) -> None:
    if not message.from_user:
        return
    context = dialogue_context_store.get(message.from_user.id)
    if not context or not context.recommended_products:
        await message.answer(
            "Сначала подберем варианты. Напишите параметры: рост, бюджет, мониторы.",
            reply_markup=main_menu_keyboard(),
        )
        return
    ids = ", ".join(context.recommended_products)
    await message.answer(
        f"Сравнение по последней подборке ({ids}):\n"
        "- устойчивость: лучше модели с 2 моторами\n"
        "- нагрузка: для тяжелого сетапа ориентируйтесь на 100+ кг\n"
        "- цена: можно сместиться в бюджетный сегмент, если уменьшить размер столешницы",
        reply_markup=recommendation_ready_keyboard(),
    )


@router.message(F.text == "Почему этот стол?")
async def explain_choice(message: Message) -> None:
    if not message.from_user:
        return
    context = dialogue_context_store.get(message.from_user.id)
    if not context or not context.recommended_products:
        await message.answer(
            "Пока нет выбранного варианта. Могу подобрать 2-3 модели и объяснить разницу."
        )
        return
    await message.answer(
        "Выбранный вариант обычно лучше по стабильности, "
        "диапазону высот и нагрузке под ваш сценарий. "
        "Если хотите, предложу более бюджетную альтернативу.",
        reply_markup=recommendation_ready_keyboard(),
    )


@router.message(F.text == "Есть дешевле?")
async def cheaper_option(message: Message) -> None:
    await message.answer(
        "Есть более бюджетные модели. "
        "Уточните минимально допустимый размер и количество мониторов, "
        "и я пересчитаю подбор.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text)
async def free_text_dialogue(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    current_state = await state.get_state()
    if current_state is not None:
        return
    user_id = message.from_user.id
    context = dialogue_context_store.get(user_id)
    if context is None:
        context = DialogueContext(user_id=user_id, known_params=KnownClientParams())
        dialogue_context_store[user_id] = context

    response = dialogue_service.handle(message.text or "", context)
    log_dialogue_event(
        phase="dialogue_processed",
        function_name="free_text_dialogue",
        user_id=user_id,
        question=message.text,
        answer=response.text,
        bot_id=_bot_id(message),
        extra={"intent": response.intent, "goal": response.goal},
    )
    if response.reset_context:
        _reset_user_context(user_id)
        await message.answer(response.text, reply_markup=main_menu_keyboard())
        log_dialogue_event(
            phase="bot_answer",
            function_name="free_text_dialogue",
            user_id=user_id,
            answer=response.text,
            bot_id=_bot_id(message),
        )
        return
    if response.start_lead_flow:
        summary = context.get_context_summary()
        await state.update_data(
            budget=context.known_params.budget_max,
            height_cm=context.known_params.height_cm,
            monitors_count=context.known_params.monitors_count,
            use_case=context.known_params.use_case,
            has_pc_case=context.known_params.has_pc_case,
            recommended_products=context.recommended_products,
            known_params=summary["known_params"],
            recent_dialogue_summary=summary["recent_dialogue_summary"],
            recent_questions=summary["recent_questions"],
            assistant_comment=(
                "Клиент запросил передачу менеджеру после консультации "
                "в свободном диалоге."
            ),
            lead_short_flow=True,
        )
        await message.answer(response.text)
        log_dialogue_event(
            phase="bot_answer",
            function_name="free_text_dialogue",
            user_id=user_id,
            answer=response.text,
            bot_id=_bot_id(message),
        )
        await state.set_state(LeadCollectionStates.name)
        return

    if context.recommended_products:
        summary = context.get_context_summary()
        last_recommendation_context[user_id] = {
            "budget": context.known_params.budget_max,
            "height_cm": context.known_params.height_cm,
            "monitors_count": context.known_params.monitors_count,
            "use_case": context.known_params.use_case,
            "recommended_products": context.recommended_products,
            "known_params": summary["known_params"],
            "recent_dialogue_summary": summary["recent_dialogue_summary"],
            "recent_questions": summary["recent_questions"],
            "assistant_comment": (
                "Клиент получил рекомендации в свободном диалоге. "
                "Нужна квалификация перед финальным оффером."
            ),
        }
        await message.answer(response.text, reply_markup=recommendation_ready_keyboard())
        log_dialogue_event(
            phase="bot_answer",
            function_name="free_text_dialogue",
            user_id=user_id,
            answer=response.text,
            bot_id=_bot_id(message),
            extra={"recommended_products": context.recommended_products},
        )
        return
    await message.answer(response.text, reply_markup=main_menu_keyboard())
    log_dialogue_event(
        phase="bot_answer",
        function_name="free_text_dialogue",
        user_id=user_id,
        answer=response.text,
        bot_id=_bot_id(message),
    )
