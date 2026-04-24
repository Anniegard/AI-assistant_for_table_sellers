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
    _ACCESSORY_CATEGORIES = {"accessory", "accessories"}

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

    @classmethod
    def _is_accessory(cls, category: str) -> bool:
        return (category or "").strip().lower() in cls._ACCESSORY_CATEGORIES

    def _build_recommendation_query(self, context: DialogueContext) -> RecommendationQuery:
        monitors_count = context.known_params.monitors_count or 2
        return RecommendationQuery(
            budget=context.known_params.budget_max,
            user_height_cm=context.known_params.height_cm,
            monitors_count=monitors_count,
            use_case=context.known_params.use_case,
            has_pc_case=context.known_params.has_pc_case,
            include_accessories=False,
            strict_budget=True,
        )

    def _format_main_recommendation_text(
        self,
        context: DialogueContext,
        ranked: list,
        explanations: dict[str, str],
        *,
        cheaper_intro: str | None = None,
    ) -> str:
        lines: list[str] = []
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
        if cheaper_intro:
            lines.append(cheaper_intro)
        if context.known_params.monitors_count is None:
            lines.append(
                "Количество мониторов вы не указали, поэтому сделаю предварительный "
                "подбор для 1-2 мониторов."
            )
        lines.append("")
        lines.append("Подойдут такие варианты:")
        for idx, item in enumerate(ranked, start=1):
            lines.append(f"{idx}. {item.product.name}: {item.product.price} ₽")
            lines.append(f"Почему подходит: {item.reasons[0]}.")
            if context.known_params.monitors_count is None:
                lines.append("Если у вас 2+ монитора, лучше уточнить размер столешницы.")
            elif item.tradeoffs:
                lines.append(f"Компромисс: {item.tradeoffs[0]}.")
            explanation = explanations.get(item.product.id, "").strip()
            if explanation:
                lines.append(f"Комментарий: {explanation}")
            lines.append("")
        lines.append(
            "Могу сравнить эти варианты, подобрать дешевле, ответить на вопросы "
            "или помочь оставить заявку менеджеру."
        )
        lines.append(
            "Дополнительно можно рассмотреть аксессуары: лоток для кабелей, "
            "держатель системного блока, кронштейн для монитора."
        )
        return "\n".join(lines).strip()

    def _build_cheaper_response(
        self, context: DialogueContext, intent: DialogueIntent
    ) -> AssistantResponse:
        if not context.recommended_products:
            return ResponseBuilder.plain(
                "Уточните параметры, и я сразу подберу более бюджетные варианты: рост и бюджет.",
                goal=AssistantGoal.ASK_MISSING_PARAM,
                intent=intent,
            )
        previous_products = self.recommendation_service.get_products_by_ids(
            context.recommended_products
        )
        previous_desks = [
            product for product in previous_products if not self._is_accessory(product.category)
        ]
        if not previous_desks:
            return ResponseBuilder.plain(
                "Пока нет предыдущей подборки столов. "
                "Напишите рост и бюджет, и я пересчитаю варианты.",
                goal=AssistantGoal.ASK_MISSING_PARAM,
                intent=intent,
            )
        previous_min_price = min(product.price for product in previous_desks)
        reduced_budget = int((context.known_params.budget_max or previous_min_price) * 0.8)
        target_max_price = min(previous_min_price - 1, reduced_budget)
        if target_max_price <= 0:
            target_max_price = previous_min_price - 1
        query = self._build_recommendation_query(context)
        query.max_price_override = target_max_price
        query.exclude_product_ids = set(context.recommended_products)
        ranked = self.recommendation_service.get_ranked_recommendations(query)
        ranked = [
            item
            for item in ranked
            if item.product.price < previous_min_price
            and item.product.id not in set(context.recommended_products)
        ]
        if not ranked:
            return ResponseBuilder.with_cta(
                (
                    "Дешевле подходящих регулируемых столов в каталоге сейчас нет. "
                    "Самый близкий бюджетный вариант уже в последней подборке. "
                    "Можно снизить цену за счет одного мотора или меньшей столешницы."
                ),
                goal=AssistantGoal.HANDLE_OBJECTION,
                intent=intent,
                cta="Сравнить варианты",
            )
        context.recommended_products = [item.product.id for item in ranked]
        explanations = self.explanation_service.explain_products(
            [item.product for item in ranked],
            query_context=asdict(query),
        )
        cheaper_intro = (
            f"Посмотрел варианты дешевле. В каталоге есть столы до {target_max_price:,} ₽."
        ).replace(",", " ")
        text = self._format_main_recommendation_text(
            context,
            ranked,
            explanations,
            cheaper_intro=cheaper_intro,
        )
        return ResponseBuilder.with_cta(
            text,
            goal=AssistantGoal.RECOMMEND,
            intent=intent,
            cta="Сравнить варианты",
        )

    @staticmethod
    def _format_price(value: int) -> str:
        if value <= 0:
            return "цена не указана в демо-базе"
        return f"{value:,} ₽".replace(",", " ")

    def _build_compare_response(
        self, context: DialogueContext, intent: DialogueIntent
    ) -> AssistantResponse:
        if not context.recommended_products:
            return ResponseBuilder.plain(
                "Сначала подберу варианты под ваш рост и бюджет. "
                "Напишите, например: рост 190, бюджет 50000.",
                goal=AssistantGoal.ASK_MISSING_PARAM,
                intent=intent,
            )
        recommended = self.recommendation_service.get_products_by_ids(context.recommended_products)
        ranked = [
            product
            for product in recommended
            if self.recommendation_service.recommender._normalized_category(product.category)
            == "adjustable_desk"
        ]
        if not ranked:
            return ResponseBuilder.plain(
                "Сейчас в контексте нет последних рекомендованных столов. "
                "Давайте сначала обновим подбор по росту и бюджету.",
                goal=AssistantGoal.ASK_MISSING_PARAM,
                intent=intent,
            )

        by_price = sorted(ranked, key=lambda item: (item.price <= 0, item.price or 10**9))
        by_stability = sorted(
            ranked, key=lambda item: (item.motors_count, item.lifting_capacity_kg), reverse=True
        )
        by_balance = sorted(
            ranked, key=lambda item: (item.price <= 0, item.price, -item.motors_count)
        )
        budget_hint = (
            f" и бюджета до {context.known_params.budget_max:,} ₽".replace(",", " ")
            if context.known_params.budget_max
            else ""
        )
        if context.known_params.height_cm:
            height_hint = f"Для вашего роста {context.known_params.height_cm} см{budget_hint}"
        else:
            height_hint = "По текущим параметрам"
        best_balance = by_balance[0]
        lines = [
            "Если коротко:",
            f"1. Самый бюджетный: {by_price[0].name} ({self._format_price(by_price[0].price)}).",
            (
                "2. Самый устойчивый: "
                f"{by_stability[0].name} ({by_stability[0].motors_count} мотора, "
                f"до {by_stability[0].lifting_capacity_kg} кг)."
            ),
            (
                "3. Лучший баланс: "
                f"{best_balance.name} ({self._format_price(best_balance.price)}, "
                f"диапазон {best_balance.min_height_cm}-{best_balance.max_height_cm} см, "
                f"столешница {best_balance.tabletop_width_cm}x{best_balance.tabletop_depth_cm} см)."
            ),
            "",
            f"{height_hint} я бы начал с {best_balance.name}.",
        ]
        return ResponseBuilder.with_cta(
            "\n".join(lines),
            goal=AssistantGoal.COMPARE,
            intent=intent,
            cta="Есть дешевле?",
        )

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
        if intent == DialogueIntent.COMPARE:
            return self._with_history(context, self._build_compare_response(context, intent))
        if intent == DialogueIntent.ACCESSORY_REQUEST:
            products = self.recommendation_service.repository.load_products()
            accessories = [
                product
                for product in products
                if product.in_stock and self._is_accessory(product.category)
            ]
            if context.known_params.use_case:
                use_case_filtered = [
                    product
                    for product in accessories
                    if context.known_params.use_case in product.use_cases
                ]
                if use_case_filtered:
                    accessories = use_case_filtered
            accessories.sort(key=lambda item: item.price)
            if not accessories:
                return self._with_history(
                    context,
                    ResponseBuilder.plain(
                        "В каталоге сейчас нет подходящих аксессуаров в наличии.",
                        goal=AssistantGoal.ANSWER_QUESTION,
                        intent=intent,
                    ),
                )
            top = accessories[:3]
            lines = ["Из аксессуаров можно рассмотреть:"]
            for product in top:
                lines.append(f"- {product.name}: {product.price} ₽")
            lines.append("Если хотите, подберу аксессуары под ваш текущий стол и сетап.")
            return self._with_history(
                context,
                ResponseBuilder.with_cta(
                    "\n".join(lines),
                    goal=AssistantGoal.ANSWER_QUESTION,
                    intent=intent,
                    cta="Подобрать стол",
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
            query = self._build_recommendation_query(context)
            ranked = self.recommendation_service.get_ranked_recommendations(query)
            if not ranked:
                over_budget_ranked: list = []
                if context.known_params.budget_max:
                    fallback_query = self._build_recommendation_query(context)
                    fallback_query.strict_budget = False
                    fallback_query.budget = None
                    fallback_query.min_price_override = context.known_params.budget_max + 1
                    over_budget_ranked = self.recommendation_service.get_ranked_recommendations(
                        fallback_query
                    )
                    over_budget_ranked.sort(
                        key=lambda item: (
                            item.product.price <= 0,
                            item.product.price if item.product.price > 0 else 10**9,
                        )
                    )
                if over_budget_ranked:
                    nearest = over_budget_ranked[:1]
                    context.recommended_products = [item.product.id for item in nearest]
                    explanations = self.explanation_service.explain_products(
                        [item.product for item in nearest],
                        query_context=asdict(query),
                    )
                    warning = (
                        "В указанном бюджете вариантов не нашлось. "
                        "Покажу ближайший вариант чуть выше бюджета с пометкой."
                    )
                    text = self._format_main_recommendation_text(
                        context,
                        nearest,
                        explanations,
                        cheaper_intro=warning,
                    )
                    return self._with_history(
                        context,
                        ResponseBuilder.with_cta(
                            text,
                            goal=AssistantGoal.RECOMMEND,
                            intent=intent,
                            cta="Сравнить варианты",
                        ),
                    )
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
            text = self._format_main_recommendation_text(context, ranked, explanations)
            return self._with_history(
                context,
                ResponseBuilder.with_cta(
                    text,
                    goal=AssistantGoal.RECOMMEND,
                    intent=intent,
                    cta="Сравнить варианты",
                ),
            )
        if intent == DialogueIntent.OBJECTION_PRICE:
            return self._with_history(context, self._build_cheaper_response(context, intent))

        return self._with_history(
            context,
            ResponseBuilder.plain(
                "Напишите, что важно в столе, и я подскажу варианты из каталога.",
                goal=AssistantGoal.ASK_MISSING_PARAM,
                intent=DialogueIntent.UNKNOWN,
            ),
        )
