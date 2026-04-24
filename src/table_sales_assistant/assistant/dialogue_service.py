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
        return missing

    @staticmethod
    def _build_missing_params_prompt(missing: list[str]) -> str:
        missing_set = set(missing)
        if missing_set == {"бюджет"}:
            return "Укажите бюджет в рублях, например: 50000."
        if missing_set == {"рост"}:
            return "Укажите ваш рост в сантиметрах, например: 190."
        return "Напишите рост и бюджет, например: рост 190, бюджет 50000."

    @staticmethod
    def _is_motor_faq(text: str) -> bool:
        lowered = text.lower()
        return any(
            token in lowered
            for token in (
                "два мотора",
                "2 мотора",
                "один мотор",
                "1 мотор",
                "чем два мотора",
                "зачем два мотора",
                "мотор лучше",
                "разница моторов",
            )
        )

    def _motor_faq_answer(self, context: DialogueContext) -> str:
        details: list[str] = []
        if context.known_params.height_cm:
            details.append(f"рост {context.known_params.height_cm} см")
        if context.known_params.budget_max:
            details.append(f"бюджет до {context.known_params.budget_max:,} руб".replace(",", " "))
        if context.known_params.use_case == "home_office":
            details.append("сценарий: домашнее рабочее место")
        elif context.known_params.use_case:
            details.append(f"сценарий: {context.known_params.use_case}")
        intro = f"С учетом ваших параметров ({', '.join(details)}), " if details else ""
        return (
            f"{intro}два мотора обычно дают более стабильный подъем, выше "
            "грузоподъемность и лучше подходят для тяжелой рабочей зоны: "
            "два монитора, системный блок, кронштейны, акустика. "
            "Один мотор может быть нормальным вариантом для легкого домашнего "
            "рабочего места, но если рабочая зона тяжелее и нужна устойчивость "
            "на большой высоте, я бы в первую очередь смотрел модели с двумя моторами."
        )

    @staticmethod
    def _with_history(context: DialogueContext, response: AssistantResponse) -> AssistantResponse:
        context.add_assistant_message(response.text)
        return response

    def handle(self, text: str, context: DialogueContext) -> AssistantResponse:
        context.add_user_message(text)
        if text.strip():
            context.recent_questions.append(text.strip())
            context.recent_questions = context.recent_questions[-10:]
        self._update_context_from_text(text, context)
        intent = self.intent_router.route(text)

        if intent == DialogueIntent.RESTART:
            return self._with_history(
                context,
                AssistantResponse(
                    text=(
                        "Начинаем заново. Напишите задачу и параметры: "
                        "бюджет, рост, мониторы и сценарий."
                    ),
                    goal=AssistantGoal.ASK_MISSING_PARAM,
                    intent=intent,
                    reset_context=True,
                ),
            )
        if intent in (DialogueIntent.LEAVE_LEAD, DialogueIntent.HANDOFF_MANAGER):
            known: list[str] = []
            if context.known_params.height_cm:
                known.append(f"рост {context.known_params.height_cm} см")
            if context.known_params.budget_max:
                known.append(
                    f"бюджет до {context.known_params.budget_max:,} руб".replace(",", " ")
                )
            if context.known_params.use_case == "home_office":
                known.append("сценарий: домашнее рабочее место")
            elif context.known_params.use_case:
                known.append(f"сценарий: {context.known_params.use_case}")
            if context.recommended_products:
                lead_text = "Отлично, помогу оставить заявку менеджеру. Как вас зовут?"
            elif known:
                lead_text = (
                    "Хорошо, помогу оставить заявку менеджеру. "
                    f"Я уже вижу параметры: {', '.join(known)}. Как вас зовут?"
                )
            else:
                lead_text = "Отлично, помогу оставить заявку менеджеру. Как вас зовут?"
            return self._with_history(
                context,
                AssistantResponse(
                    text=lead_text,
                    goal=AssistantGoal.COLLECT_LEAD,
                    intent=intent,
                    start_lead_flow=True,
                ),
            )
        if intent in (DialogueIntent.FAQ, DialogueIntent.DELIVERY_WARRANTY_MATERIALS):
            if self._is_motor_faq(text):
                return self._with_history(
                    context,
                    ResponseBuilder.with_cta(
                        (
                            f"{self._motor_faq_answer(context)}\n\n"
                            "Если хотите, сравню подходящие варианты по устойчивости, "
                            "нагрузке и цене."
                        ),
                        goal=AssistantGoal.ANSWER_QUESTION,
                        intent=DialogueIntent.FAQ,
                        cta="Сравнить варианты",
                    ),
                )
            answer = self.faq_service.answer(text)
            if answer:
                known = []
                if context.known_params.height_cm:
                    known.append(f"рост {context.known_params.height_cm} см")
                if context.known_params.budget_max:
                    known.append(f"бюджет до {context.known_params.budget_max} руб")
                known_params_hint = (
                    f" Уже вижу параметры: {', '.join(known)}."
                    if known
                    else ""
                )
                return self._with_history(
                    context,
                    ResponseBuilder.with_cta(
                        (
                            f"{answer}\n\n"
                            "Если хотите, могу сразу подобрать 2-3 варианта "
                            f"под ваши параметры.{known_params_hint}"
                        ),
                        goal=AssistantGoal.ANSWER_QUESTION,
                        intent=intent,
                        cta="Подобрать стол",
                    ),
                )
            return self._with_history(
                context,
                ResponseBuilder.with_cta(
                    (
                        "Точного ответа в базе знаний нет. "
                        "Могу уточнить у менеджера и передать ваш запрос."
                    ),
                    goal=AssistantGoal.HANDOFF_READY,
                    intent=intent,
                    cta="Позвать менеджера",
                ),
            )
        if intent == DialogueIntent.SMALL_TALK:
            return self._with_history(
                context,
                ResponseBuilder.with_cta(
                    (
                        "Я помогу выбрать регулируемый стол под вашу задачу. "
                        "Напишите параметры: рост и бюджет (мониторы - по желанию)."
                    ),
                    goal=AssistantGoal.ASK_MISSING_PARAM,
                    intent=intent,
                    cta="Подобрать стол",
                ),
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
                return self._with_history(
                    context,
                    ResponseBuilder.plain(
                        self._build_missing_params_prompt(missing),
                        goal=AssistantGoal.ASK_MISSING_PARAM,
                        intent=intent,
                    ),
                )
            monitors_count = context.known_params.monitors_count or 2
            query = RecommendationQuery(
                budget=context.known_params.budget_max,
                user_height_cm=context.known_params.height_cm,
                monitors_count=monitors_count,
                use_case=context.known_params.use_case,
                has_pc_case=context.known_params.has_pc_case,
            )
            ranked = self.recommendation_service.get_ranked_recommendations(query)
            if not ranked:
                return self._with_history(
                    context,
                    ResponseBuilder.with_cta(
                        (
                            "По этим данным вариантов нет в наличии. "
                            "Могу предложить похожие модели с чуть большим бюджетом."
                        ),
                        goal=AssistantGoal.ASK_MISSING_PARAM,
                        intent=intent,
                        cta="Есть дешевле?",
                    ),
                )
            context.recommended_products = [item.product.id for item in ranked]
            products = [item.product for item in ranked]
            explanations = self.explanation_service.explain_products(
                products,
                query_context=asdict(query),
            )
            lines = []
            intro_parts: list[str] = []
            if context.known_params.height_cm:
                intro_parts.append(f"рост {context.known_params.height_cm} см")
            if context.known_params.budget_max:
                intro_parts.append(
                    f"бюджет до {context.known_params.budget_max:,} рублей".replace(",", " ")
                )
            if context.known_params.use_case == "home_office":
                intro_parts.append("сценарий: домашнее рабочее место")
            elif context.known_params.use_case:
                intro_parts.append(f"сценарий: {context.known_params.use_case}")
            if intro_parts:
                lines.append(f"Понял: {', '.join(intro_parts)}.")
            lines.append("Вот несколько вариантов из каталога:")
            if context.known_params.monitors_count is None:
                lines.append(
                    "Количество мониторов вы не указали, поэтому сделаю предварительный "
                    "подбор для 1-2 мониторов."
                )
            for item in ranked:
                lines.append(
                    f"- {item.product.name} ({item.product.price} руб, fit {item.fit_score}): "
                    f"{item.reasons[0]}. Компромисс: "
                    f"{item.tradeoffs[0] if item.tradeoffs else 'без явных компромиссов'}"
                )
            first_id = ranked[0].product.id
            lines.append(f"\nПочему подходит: {explanations.get(first_id, '')}")
            lines.append(
                "Могу сравнить эти варианты, подобрать дешевле, ответить на вопросы "
                "или помочь оставить заявку менеджеру."
            )
            return self._with_history(
                context,
                ResponseBuilder.with_cta(
                    "\n".join(lines),
                    goal=AssistantGoal.RECOMMEND,
                    intent=intent,
                    cta="Сравнить варианты",
                ),
            )

        return self._with_history(
            context,
            ResponseBuilder.plain(
                "Напишите, что важно в столе, и я подскажу варианты из каталога.",
                goal=AssistantGoal.ASK_MISSING_PARAM,
                intent=DialogueIntent.UNKNOWN,
            ),
        )
