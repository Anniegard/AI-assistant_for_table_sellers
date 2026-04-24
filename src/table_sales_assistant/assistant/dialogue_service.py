from dataclasses import asdict

from table_sales_assistant.assistant.intent_router import IntentRouter
from table_sales_assistant.assistant.models import (
    AssistantGoal,
    AssistantResponse,
    DialogueContext,
    DialogueIntent,
)
from table_sales_assistant.assistant.parsing import (
    extract_budget_range,
    extract_has_pc_case,
    extract_height_cm,
    extract_monitors_count,
    extract_use_case,
)
from table_sales_assistant.assistant.response_builder import ResponseBuilder
from table_sales_assistant.catalog.recommender import RecommendationQuery
from table_sales_assistant.services.explanation_service import ExplanationService
from table_sales_assistant.services.faq_service import FAQService
from table_sales_assistant.services.recommendation_service import RecommendationService


class DialogueService:
    def __init__(
        self,
        recommendation_service: RecommendationService,
        faq_service: FAQService,
        explanation_service: ExplanationService,
        intent_router: IntentRouter | None = None,
    ) -> None:
        self.recommendation_service = recommendation_service
        self.faq_service = faq_service
        self.explanation_service = explanation_service
        self.intent_router = intent_router or IntentRouter()

    def _update_context_from_text(self, text: str, context: DialogueContext) -> None:
        height = extract_height_cm(text)
        if height is not None:
            context.known_params.height_cm = height
        monitors = extract_monitors_count(text)
        if monitors is not None:
            context.known_params.monitors_count = monitors
        budget_min, budget_max = extract_budget_range(text)
        if budget_min is not None:
            context.known_params.budget_min = budget_min
        if budget_max is not None:
            context.known_params.budget_max = budget_max
        use_case = extract_use_case(text)
        if use_case is not None:
            context.known_params.use_case = use_case
        has_pc_case = extract_has_pc_case(text)
        if has_pc_case is not None:
            context.known_params.has_pc_case = has_pc_case

    def _missing_params(self, context: DialogueContext) -> list[str]:
        missing: list[str] = []
        if context.known_params.budget_max is None:
            missing.append("бюджет")
        if context.known_params.height_cm is None:
            missing.append("рост")
        if context.known_params.monitors_count is None:
            missing.append("количество мониторов")
        return missing

    def handle(self, text: str, context: DialogueContext) -> AssistantResponse:
        if text.strip():
            context.recent_questions.append(text.strip())
            context.recent_questions = context.recent_questions[-10:]
        self._update_context_from_text(text, context)
        intent = self.intent_router.route(text)

        if intent == DialogueIntent.RESTART:
            return AssistantResponse(
                text=(
                    "Начинаем заново. Напишите задачу и параметры: "
                    "бюджет, рост, мониторы и сценарий."
                ),
                goal=AssistantGoal.ASK_MISSING_PARAM,
                intent=intent,
                reset_context=True,
            )
        if intent in (DialogueIntent.LEAVE_LEAD, DialogueIntent.HANDOFF_MANAGER):
            return AssistantResponse(
                text="Отлично, помогу оставить заявку менеджеру. Как вас зовут?",
                goal=AssistantGoal.COLLECT_LEAD,
                intent=intent,
                start_lead_flow=True,
            )
        if intent in (DialogueIntent.FAQ, DialogueIntent.DELIVERY_WARRANTY_MATERIALS):
            answer = self.faq_service.answer(text)
            if answer:
                return ResponseBuilder.with_cta(
                    (
                        f"{answer}\n\n"
                        "Если хотите, могу сразу подобрать 2-3 варианта "
                        "под ваши параметры."
                    ),
                    goal=AssistantGoal.ANSWER_QUESTION,
                    intent=intent,
                    cta="Подобрать стол",
                )
            return ResponseBuilder.with_cta(
                (
                    "Точного ответа в базе знаний нет. "
                    "Могу уточнить у менеджера и передать ваш запрос."
                ),
                goal=AssistantGoal.HANDOFF_READY,
                intent=intent,
                cta="Позвать менеджера",
            )
        if intent == DialogueIntent.SMALL_TALK:
            return ResponseBuilder.with_cta(
                (
                    "Я помогу выбрать регулируемый стол под вашу задачу. "
                    "Напишите параметры: рост, бюджет и количество мониторов."
                ),
                goal=AssistantGoal.ASK_MISSING_PARAM,
                intent=intent,
                cta="Подобрать стол",
            )

        if intent in (
            DialogueIntent.RECOMMEND,
            DialogueIntent.UNKNOWN,
            DialogueIntent.CLARIFY_RECOMMENDATION,
            DialogueIntent.OBJECTION_PRICE,
            DialogueIntent.COMPARE,
        ):
            missing = self._missing_params(context)
            if missing and intent in (DialogueIntent.RECOMMEND, DialogueIntent.UNKNOWN):
                return ResponseBuilder.plain(
                    f"Чтобы подобрать стол точнее, уточните: {', '.join(missing)}.",
                    goal=AssistantGoal.ASK_MISSING_PARAM,
                    intent=intent,
                )
            query = RecommendationQuery(
                budget=context.known_params.budget_max,
                user_height_cm=context.known_params.height_cm,
                monitors_count=context.known_params.monitors_count,
                use_case=context.known_params.use_case,
                has_pc_case=context.known_params.has_pc_case,
            )
            ranked = self.recommendation_service.get_ranked_recommendations(query)
            if not ranked:
                return ResponseBuilder.with_cta(
                    (
                        "По этим данным вариантов нет в наличии. "
                        "Могу предложить похожие модели с чуть большим бюджетом."
                    ),
                    goal=AssistantGoal.ASK_MISSING_PARAM,
                    intent=intent,
                    cta="Есть дешевле?",
                )
            context.recommended_products = [item.product.id for item in ranked]
            products = [item.product for item in ranked]
            explanations = self.explanation_service.explain_products(
                products,
                query_context=asdict(query),
            )
            lines = ["Подобрал 2-3 варианта: бюджетный, сбалансированный и с запасом."]
            for item in ranked:
                lines.append(
                    f"- {item.product.name} ({item.product.price} руб, fit {item.fit_score}): "
                    f"{item.reasons[0]}. Компромисс: "
                    f"{item.tradeoffs[0] if item.tradeoffs else 'без явных компромиссов'}"
                )
            first_id = ranked[0].product.id
            lines.append(f"\nПочему подходит: {explanations.get(first_id, '')}")
            lines.append("Хотите, сравню варианты по устойчивости, цене и нагрузке?")
            return ResponseBuilder.with_cta(
                "\n".join(lines),
                goal=AssistantGoal.RECOMMEND,
                intent=intent,
                cta="Сравнить варианты",
            )

        return ResponseBuilder.plain(
            "Напишите, что важно в столе, и я подскажу варианты из каталога.",
            goal=AssistantGoal.ASK_MISSING_PARAM,
            intent=DialogueIntent.UNKNOWN,
        )
