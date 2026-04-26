from dataclasses import fields

from table_sales_assistant.assistant.collection import (
    ASK_ASSEMBLY_STEP_TEXT,
    ASK_BUDGET_STEP_TEXT,
    ASK_CITY_STEP_TEXT,
    ASK_HEIGHT_STEP_TEXT,
    ASK_MONITORS_STEP_TEXT,
    ASK_PC_STEP_TEXT,
    ASK_SCENARIO_TEXT,
    ASK_SIZE_STEP_TEXT,
    LABEL_TO_SCENARIO,
    STEP_BUDGET,
    STEP_HEIGHT,
    STEP_MONITORS,
    STEP_PC,
    STEP_SCENARIO,
    STEP_SIZE,
    STEP_CITY,
    STEP_ASSEMBLY,
)
from table_sales_assistant.assistant.free_text_parser import (
    ACTIVE_STEP_BUDGET,
    ACTIVE_STEP_HEIGHT,
    ACTIVE_STEP_MONITORS,
    ACTIVE_STEP_SIZE,
    ParsedSignals,
    is_dismissal_reply,
    parse_budget_from_text,
    parse_internal_scenario,
    parse_signals,
)
from table_sales_assistant.assistant.intent_router import IntentRouter
from table_sales_assistant.assistant.models import (
    AssistantGoal,
    AssistantResponse,
    DialogueContext,
    DialogueIntent,
    KnownClientParams,
)
from table_sales_assistant.assistant.response_builder import ResponseBuilder
from table_sales_assistant.assistant.scenario_labels import scenario_label_ru
from table_sales_assistant.catalog.recommender import RecommendationQuery
from table_sales_assistant.catalog.scenario_mapping import catalog_tags_for_scenario
from table_sales_assistant.services.explanation_service import ExplanationService
from table_sales_assistant.services.faq_service import FAQService
from table_sales_assistant.services.recommendation_service import RecommendationService


def _first_missing_collection_step(kp: KnownClientParams) -> str | None:
    if kp.use_case is None:
        return STEP_SCENARIO
    if kp.height_cm is None and not kp.height_unspecified:
        return STEP_HEIGHT
    if (
        kp.budget_max is None
        and kp.budget_min is None
        and not kp.budget_unspecified
    ):
        return STEP_BUDGET
    if kp.monitors_count is None and not kp.monitors_unspecified:
        return STEP_MONITORS
    if kp.has_pc_case is None and not kp.pc_unspecified:
        return STEP_PC
    if (
        not kp.no_size_limit
        and kp.max_width_cm is None
        and kp.preferred_width_cm is None
        and not kp.size_unspecified
    ):
        return STEP_SIZE
    return None


def _parser_active_step_for_collection(missing: str | None) -> str | None:
    if missing == STEP_HEIGHT:
        return ACTIVE_STEP_HEIGHT
    if missing == STEP_BUDGET:
        return ACTIVE_STEP_BUDGET
    if missing == STEP_MONITORS:
        return ACTIVE_STEP_MONITORS
    if missing == STEP_SIZE:
        return ACTIVE_STEP_SIZE
    return None


def _height_ergonomic_sentence(height_cm: int | None) -> str:
    if height_cm is None:
        return ""
    if 165 <= height_cm <= 185:
        return (
            " Ваш рост подходит под большинство регулируемых столов, поэтому основной выбор "
            "зависит от бюджета, размера, нагрузки и сценария."
        )
    if height_cm >= 190:
        return (
            " При таком росте важно проверить максимальную высоту и устойчивость "
            "в верхнем положении."
        )
    if height_cm < 165:
        return (
            " При таком росте особенно важна минимальная высота, чтобы стол был удобен "
            "в сидячем положении."
        )
    return ""


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

    def _reset_session(self, context: DialogueContext) -> None:
        context.known_params = KnownClientParams()
        context.recommended_products = []
        context.recent_questions = []
        context.recent_messages = []
        context.collection_answered.clear()
        context.guide_active = True
        context.low_budget_warned = False
        context.awaiting_budget_after_cheaper = False
        context.manager_summary = ""
        context.dialogue_goal = None
        context.lead_flow_active = False
        context.lead_step = None
        context.lead_name = None
        context.lead_phone = None
        context.lead_city = None
        context.lead_comment = None

    def _merge_signals_into_params(
        self, context: DialogueContext, signals: ParsedSignals, raw_text: str
    ) -> None:
        kp = context.known_params
        if signals.height_cm is not None:
            kp.height_cm = signals.height_cm
            kp.height_unspecified = False
        if signals.budget_min is not None:
            kp.budget_min = signals.budget_min
        if signals.budget_max is not None:
            kp.budget_max = signals.budget_max
            kp.budget_exact_rub = signals.budget_exact
        if signals.monitors_count is not None:
            kp.monitors_count = signals.monitors_count
            kp.monitors_unspecified = False
        if signals.has_pc_on_table is not None:
            kp.has_pc_case = signals.has_pc_on_table
            kp.pc_unspecified = False
        if signals.internal_scenario is not None:
            kp.use_case = signals.internal_scenario
        if signals.preferred_width_cm is not None:
            kp.preferred_width_cm = signals.preferred_width_cm
        if signals.preferred_depth_cm is not None:
            kp.preferred_depth_cm = signals.preferred_depth_cm
        if signals.max_width_cm is not None:
            kp.max_width_cm = signals.max_width_cm
        if signals.max_depth_cm is not None:
            kp.max_depth_cm = signals.max_depth_cm
        if signals.no_size_limit:
            kp.no_size_limit = True
            kp.size_unspecified = False
        if signals.heavy_setup:
            kp.heavy_setup = True
        raw_lower = (raw_text or "").strip().lower()
        if raw_lower in ("москва", "санкт-петербург"):
            kp.city = raw_text.strip()
        if "другой город" in raw_lower:
            kp.city = None
        if raw_lower in ("да", "нужна сборка"):
            kp.needs_assembly = True
        elif raw_lower in ("нет", "без сборки"):
            kp.needs_assembly = False
        elif raw_lower in ("пока не знаю", "не знаю"):
            kp.needs_assembly = False

        mapped = LABEL_TO_SCENARIO.get((raw_text or "").strip().lower())
        if mapped is not None:
            kp.use_case = mapped
        elif parse_internal_scenario(raw_text):
            kp.use_case = parse_internal_scenario(raw_text)

    def _apply_dismissal_for_current_step(
        self, context: DialogueContext, text: str, signals: ParsedSignals
    ) -> None:
        if not is_dismissal_reply(text):
            return
        kp = context.known_params
        missing = _first_missing_collection_step(kp)
        if missing == STEP_SCENARIO and signals.internal_scenario is None:
            kp.use_case = "unknown"
        elif missing == STEP_HEIGHT and signals.height_cm is None:
            kp.height_unspecified = True
        elif missing == STEP_BUDGET and signals.budget_max is None and signals.budget_min is None:
            kp.budget_unspecified = True
        elif missing == STEP_MONITORS and signals.monitors_count is None:
            kp.monitors_unspecified = True
        elif missing == STEP_PC and signals.has_pc_on_table is None:
            kp.pc_unspecified = True
        elif missing == STEP_SIZE:
            kp.size_unspecified = True
        elif missing == STEP_CITY:
            kp.city = "Пока не знаю"
        elif missing == STEP_ASSEMBLY:
            kp.needs_assembly = None

    def _apply_combined_free_text_shortcut(self, context: DialogueContext, text: str) -> None:
        lowered = text.lower()
        kp = context.known_params
        _bm, bx_budget, _ = parse_budget_from_text(text)
        rich = "рост" in lowered and (
            "бюджет" in lowered or "руб" in lowered or "тыс" in lowered or bool(bx_budget)
        )
        pick_desk = "подбери" in lowered or "подобрать" in lowered or "нужен стол" in lowered
        if not (rich or (pick_desk and kp.height_cm and (kp.budget_max or kp.budget_min))):
            return
        if kp.use_case is None and pick_desk:
            kp.use_case = "unknown"

    def _update_context_from_text(self, text: str, context: DialogueContext) -> None:
        missing = _first_missing_collection_step(context.known_params)
        active = _parser_active_step_for_collection(
            missing if context.guide_active and not context.recommended_products else None
        )
        signals = parse_signals(text, active_step=active)
        self._merge_signals_into_params(context, signals, text)
        self._apply_dismissal_for_current_step(context, text, signals)
        self._apply_combined_free_text_shortcut(context, text)
        self._apply_partial_params_completion(context, text)

    def _apply_partial_params_completion(self, context: DialogueContext, text: str) -> None:
        bm, bx, _ = parse_budget_from_text(text)
        if bm is None and bx is None:
            return
        kp = context.known_params
        if not kp.height_cm:
            return
        if kp.use_case is None:
            kp.use_case = "unknown"

    def _missing_legacy_budget_height(self, context: DialogueContext) -> list[str]:
        missing: list[str] = []
        kp = context.known_params
        if not kp.budget_unspecified and kp.budget_max is None and kp.budget_min is None:
            missing.append("бюджет")
        if not kp.height_unspecified and kp.height_cm is None:
            missing.append("рост")
        return missing

    @staticmethod
    def _build_missing_params_prompt(missing: list[str]) -> str:
        missing_set = set(missing)
        if missing_set == {"бюджет"}:
            return ASK_BUDGET_STEP_TEXT
        if missing_set == {"рост"}:
            return ASK_HEIGHT_STEP_TEXT
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
        kp = context.known_params
        if kp.height_cm:
            details.append(f"рост {kp.height_cm} см")
        if kp.budget_max:
            details.append(f"бюджет до {kp.budget_max:,} руб".replace(",", " "))
        if kp.use_case:
            details.append(f"сценарий: {scenario_label_ru(kp.use_case)}")
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
        kp = context.known_params
        monitors = kp.monitors_count if kp.monitors_count is not None else 2
        cap: int | None
        if kp.budget_unspecified:
            cap = None
        else:
            cap = kp.budget_max
            if cap is None and kp.budget_min is not None:
                cap = int(kp.budget_min * 1.5)
        return RecommendationQuery(
            budget=cap,
            budget_min_rub=kp.budget_min,
            budget_max_rub=None if kp.budget_unspecified else kp.budget_max,
            user_height_cm=kp.height_cm,
            ignore_user_height_hard_filter=bool(kp.height_unspecified),
            monitors_count=monitors,
            use_case=kp.use_case or "unknown",
            has_pc_case=kp.has_pc_case,
            heavy_setup=bool(kp.heavy_setup),
            max_width_cm=kp.max_width_cm,
            max_depth_cm=kp.max_depth_cm,
            no_size_limit=kp.no_size_limit,
            include_accessories=False,
            strict_budget=True,
        )

    @staticmethod
    def _sanitize_query_context(query: RecommendationQuery) -> dict[str, object]:
        data = {f.name: getattr(query, f.name) for f in fields(query)}
        data["scenario"] = scenario_label_ru(query.use_case)
        data.pop("use_case", None)
        return data

    @staticmethod
    def _known_params_for_text(context: DialogueContext) -> list[str]:
        kp = context.known_params
        params: list[str] = []
        if kp.height_cm:
            params.append(f"рост {kp.height_cm} см")
        if kp.budget_max or kp.budget_min:
            if kp.budget_min and kp.budget_max:
                params.append(
                    f"бюджет {kp.budget_min:,}–{kp.budget_max:,} ₽".replace(",", " ")
                )
            elif kp.budget_max:
                params.append(f"бюджет до {kp.budget_max:,} ₽".replace(",", " "))
            elif kp.budget_min:
                params.append(f"бюджет от {kp.budget_min:,} ₽".replace(",", " "))
        if kp.monitors_count is not None:
            params.append(f"мониторов: {kp.monitors_count}")
        if kp.use_case:
            params.append(f"сценарий: {scenario_label_ru(kp.use_case)}")
        if kp.city:
            params.append(f"город: {kp.city}")
        return params

    def _next_collection_prompt(self, context: DialogueContext) -> str | None:
        step = _first_missing_collection_step(context.known_params)
        prompts = {
            STEP_SCENARIO: ASK_SCENARIO_TEXT,
            STEP_HEIGHT: ASK_HEIGHT_STEP_TEXT,
            STEP_BUDGET: ASK_BUDGET_STEP_TEXT,
            STEP_MONITORS: ASK_MONITORS_STEP_TEXT,
            STEP_PC: ASK_PC_STEP_TEXT,
            STEP_SIZE: ASK_SIZE_STEP_TEXT,
            STEP_CITY: ASK_CITY_STEP_TEXT,
            STEP_ASSEMBLY: ASK_ASSEMBLY_STEP_TEXT,
        }
        return prompts.get(step or "")

    @staticmethod
    def _invalid_step_hint(step: str) -> str:
        hints = {
            STEP_HEIGHT: (
                "Не совсем понял рост. Выберите вариант кнопкой или напишите, например: 178 или 178 см."
            ),
            STEP_BUDGET: (
                "Не совсем понял бюджет. Выберите кнопкой или напишите, например: 50000, 50к, 50-80к."
            ),
            STEP_MONITORS: (
                "Не совсем понял количество мониторов. Выберите кнопкой или напишите: 1, 2, несколько."
            ),
            STEP_PC: (
                "Не понял, где будет системный блок. Выберите: Да, Нет, Только ноутбук, Системник на полу."
            ),
            STEP_SIZE: (
                "Не совсем понял размер. Выберите вариант кнопкой или напишите, например: 120x60, 140x70, без ограничений."
            ),
            STEP_CITY: (
                "Не понял город. Выберите кнопку или напишите название города."
            ),
            STEP_ASSEMBLY: (
                "Не понял ответ по сборке. Выберите: Да, Нет или Пока не знаю."
            ),
        }
        return hints.get(step, "Не совсем понял ответ. Выберите вариант кнопкой или напишите подробнее.")

    @staticmethod
    def _is_step_value_recognized(step: str, context: DialogueContext) -> bool:
        kp = context.known_params
        if step == STEP_SCENARIO:
            return kp.use_case is not None
        if step == STEP_HEIGHT:
            return kp.height_cm is not None or kp.height_unspecified
        if step == STEP_BUDGET:
            return (kp.budget_min is not None or kp.budget_max is not None) or kp.budget_unspecified
        if step == STEP_MONITORS:
            return kp.monitors_count is not None or kp.monitors_unspecified
        if step == STEP_PC:
            return kp.has_pc_case is not None or kp.pc_unspecified
        if step == STEP_SIZE:
            return kp.no_size_limit or kp.preferred_width_cm is not None or kp.size_unspecified
        return True

    def _start_lead_flow(self, context: DialogueContext) -> AssistantResponse:
        context.lead_flow_active = True
        context.lead_step = "name"
        return AssistantResponse(
            text="Отлично, помогу оставить заявку менеджеру. Как вас зовут?",
            goal=AssistantGoal.COLLECT_LEAD,
            intent=DialogueIntent.HANDOFF_MANAGER,
            start_lead_flow=True,
        )

    def _handle_lead_flow(self, text: str, context: DialogueContext) -> AssistantResponse:
        value = text.strip()
        lowered = value.lower()
        if context.lead_step == "name":
            if not value:
                return ResponseBuilder.plain(
                    "Напишите, пожалуйста, как к вам обращаться.",
                    goal=AssistantGoal.COLLECT_LEAD,
                    intent=DialogueIntent.LEAVE_LEAD,
                )
            context.lead_name = value
            context.lead_step = "phone"
            return ResponseBuilder.plain(
                "Оставьте телефон для связи.",
                goal=AssistantGoal.COLLECT_LEAD,
                intent=DialogueIntent.LEAVE_LEAD,
            )
        if context.lead_step == "phone":
            digits = "".join(ch for ch in value if ch.isdigit())
            if len(digits) < 10:
                return ResponseBuilder.plain(
                    "Телефон выглядит неполным. Укажите номер в формате +7XXXXXXXXXX.",
                    goal=AssistantGoal.COLLECT_LEAD,
                    intent=DialogueIntent.LEAVE_LEAD,
                )
            context.lead_phone = value
            context.lead_step = "city"
            return ResponseBuilder.plain(
                "В каком городе вы находитесь?",
                goal=AssistantGoal.COLLECT_LEAD,
                intent=DialogueIntent.LEAVE_LEAD,
            )
        if context.lead_step == "city":
            if lowered in {"другой город", "пока не знаю"}:
                return ResponseBuilder.plain(
                    "Напишите, пожалуйста, город вручную.",
                    goal=AssistantGoal.COLLECT_LEAD,
                    intent=DialogueIntent.LEAVE_LEAD,
                )
            if not value:
                return ResponseBuilder.plain(
                    "Укажите город, чтобы передать заявку менеджеру.",
                    goal=AssistantGoal.COLLECT_LEAD,
                    intent=DialogueIntent.LEAVE_LEAD,
                )
            context.lead_city = value
            context.known_params.city = value
            context.lead_step = "comment"
            return ResponseBuilder.plain(
                "Если есть комментарий для менеджера — напишите его. Если нет, напишите «нет».",
                goal=AssistantGoal.COLLECT_LEAD,
                intent=DialogueIntent.LEAVE_LEAD,
            )
        if context.lead_step == "comment":
            if lowered not in {"нет", "не знаю", "пропустить", "-"}:
                context.lead_comment = value
            context.lead_flow_active = False
            context.lead_step = "done"
            return AssistantResponse(
                text="Заявка принята. Спасибо! Менеджер свяжется с вами в ближайшее время.",
                goal=AssistantGoal.HANDOFF_READY,
                intent=DialogueIntent.LEAVE_LEAD,
                start_lead_flow=False,
            )
        return ResponseBuilder.plain(
            "Готов продолжить подбор. Напишите, что важно в столе.",
            goal=AssistantGoal.ASK_MISSING_PARAM,
            intent=DialogueIntent.UNKNOWN,
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
        intro_parts = self._known_params_for_text(context)
        if intro_parts:
            lines.append(f"Понял: {', '.join(intro_parts)}.")
        ergo = _height_ergonomic_sentence(context.known_params.height_cm)
        if ergo.strip():
            lines.append(ergo.strip())
        if cheaper_intro:
            lines.append(cheaper_intro)
        kp = context.known_params
        if kp.monitors_count is None and kp.monitors_unspecified:
            pass
        elif kp.monitors_count is None:
            lines.append(
                "Пока сделаю предварительный подбор для 1–2 мониторов. "
                "Если у вас два монитора или системный блок будет стоять на столе, "
                "лучше выбрать модель с двумя моторами и запасом по грузоподъёмности."
            )
        recommendation_items: list[dict[str, str]] = []
        for item in ranked[:3]:
            reason = item.reasons[0].rstrip(".")
            tradeoff = item.tradeoffs[0].rstrip(".") if item.tradeoffs else ""
            explanation = explanations.get(item.product.id, "").strip()
            if explanation:
                reason = f"{reason}. {explanation}"
            recommendation_items.append(
                {
                    "name": item.product.name,
                    "price": f"{item.product.price:,} ₽".replace(",", " "),
                    "reason": reason,
                    "tradeoff": tradeoff.rstrip("."),
                    "confidence": ResponseBuilder._format_confidence(item.fit_score),
                }
            )
        response = ResponseBuilder.recommendation(
            intro_lines=lines,
            items=recommendation_items,
            cta="Сравнить варианты",
            intent=DialogueIntent.RECOMMEND,
        )
        return response.text

    def _build_cheaper_response(
        self, context: DialogueContext, intent: DialogueIntent, user_text: str
    ) -> AssistantResponse:
        bm, bx, _ = parse_budget_from_text(user_text)
        has_new_budget = bm is not None or bx is not None

        if has_new_budget:
            if bm is not None:
                context.known_params.budget_min = bm
            if bx is not None:
                context.known_params.budget_max = bx
            context.awaiting_budget_after_cheaper = False
            return self._rerun_recommendation(context, intent)

        context.awaiting_budget_after_cheaper = True
        return ResponseBuilder.plain(
            "В каком бюджете теперь смотреть? Например: до 50 000 ₽ или 40-60к.",
            goal=AssistantGoal.ASK_MISSING_PARAM,
            intent=intent,
        )

    def _rerun_recommendation(
        self, context: DialogueContext, intent: DialogueIntent
    ) -> AssistantResponse:
        query = self._build_recommendation_query(context)
        ranked = self.recommendation_service.get_ranked_recommendations(query)
        if not ranked:
            return ResponseBuilder.no_exact_match(
                blocking_constraint="текущая комбинация параметров",
                alternatives=[
                    "Ослабить одно ограничение и показать ближайшие варианты",
                    "Уточнить приоритет: цена, размер или устойчивость",
                ],
                intent=intent,
                cta="Позвать менеджера",
            )
        context.recommended_products = [item.product.id for item in ranked]
        explanations = self.explanation_service.explain_products(
            [item.product for item in ranked],
            query_context=self._sanitize_query_context(query),
        )
        text = self._format_main_recommendation_text(context, ranked, explanations)
        return ResponseBuilder.with_cta(
            text,
            goal=AssistantGoal.RECOMMEND,
            intent=intent,
            cta="Сравнить варианты",
        )

    def _post_rec_intent_override(
        self, text: str, intent: DialogueIntent, context: DialogueContext
    ) -> DialogueIntent:
        if not context.recommended_products:
            return intent
        lowered = text.lower()
        bm, bx, _ = parse_budget_from_text(text)
        if (bm is not None or bx is not None) and (
            "бюджет" in lowered
            or "руб" in lowered
            or "₽" in lowered
            or "тыс" in lowered
            or "к" in lowered.replace(" ", "")
            or "до " in lowered
            or "от " in lowered
            or "смотрим" in lowered
        ):
            return DialogueIntent.CHANGE_BUDGET
        if parse_internal_scenario(text) and any(
            w in lowered for w in ("вообще", "теперь", "передумал", "на самом деле", "это для")
        ):
            return DialogueIntent.CHANGE_SCENARIO
        if (
            ("мест" in lowered or "ширин" in lowered or "размер" in lowered)
            and intent == DialogueIntent.UNKNOWN
        ):
            return DialogueIntent.CHANGE_SIZE
        return intent

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
                "Сначала подберу варианты под ваши параметры. "
                "Нажмите «Подобрать стол» или опишите задачу.",
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
                "Давайте сначала обновим подбор.",
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
        budget_hint = ""
        if context.known_params.budget_max:
            budget_hint = f" и бюджета до {context.known_params.budget_max:,} ₽".replace(",", " ")
        if context.known_params.height_cm:
            height_hint = f"Для вашего роста {context.known_params.height_cm} см{budget_hint}"
        else:
            height_hint = "По текущим параметрам"
        best_balance = by_balance[0]
        return ResponseBuilder.comparison(
            bullets=[
                f"Самый бюджетный: {by_price[0].name} ({self._format_price(by_price[0].price)})",
                (
                    "Самый устойчивый: "
                    f"{by_stability[0].name} ({by_stability[0].motors_count} мотора, "
                    f"до {by_stability[0].lifting_capacity_kg} кг)"
                ),
                (
                    "Лучший баланс: "
                    f"{best_balance.name} ({self._format_price(best_balance.price)}, "
                    f"диапазон {best_balance.min_height_cm}-{best_balance.max_height_cm} см, "
                    "столешница "
                    f"{best_balance.tabletop_width_cm}x"
                    f"{best_balance.tabletop_depth_cm} см)"
                ),
            ],
            conclusion=f"{height_hint} я бы начал с {best_balance.name}.",
            cta="Есть дешевле?",
            intent=intent,
        )

    def _run_recommendation_block(
        self, context: DialogueContext, intent: DialogueIntent
    ) -> AssistantResponse:
        query = self._build_recommendation_query(context)
        ranked = self.recommendation_service.get_ranked_recommendations(query)
        if not ranked:
            return ResponseBuilder.no_exact_match(
                blocking_constraint=(
                    "жёсткий лимит бюджета"
                    if context.known_params.budget_max
                    else "текущая комбинация параметров"
                ),
                alternatives=[
                    "Ослабить одно ограничение и показать ближайшие варианты",
                    "Уточнить приоритет: цена, размер или устойчивость",
                ],
                intent=intent,
                cta="Позвать менеджера",
            )
        stretch_note = ""
        for item in ranked:
            if getattr(item, "is_budget_stretch", False):
                stretch_note = (
                    "Один из вариантов немного выше бюджета, но я добавил его как запасной, "
                    "потому что он лучше подходит под ваши условия."
                )
                break
        context.recommended_products = [item.product.id for item in ranked]
        products = [item.product for item in ranked]
        explanations = self.explanation_service.explain_products(
            products,
            query_context=self._sanitize_query_context(query),
        )
        text = self._format_main_recommendation_text(
            context, ranked, explanations, cheaper_intro=stretch_note or None
        )
        context.guide_active = False
        return ResponseBuilder.with_cta(
            text,
            goal=AssistantGoal.RECOMMEND,
            intent=intent,
            cta="Сравнить варианты",
        )

    def handle(self, text: str, context: DialogueContext) -> AssistantResponse:
        context.add_user_message(text)
        if text.strip():
            context.recent_questions.append(text.strip())
            context.recent_questions = context.recent_questions[-10:]
        missing_before = _first_missing_collection_step(context.known_params)
        self._update_context_from_text(text, context)
        intent = self.intent_router.route(text)
        intent = self._post_rec_intent_override(text, intent, context)

        if context.awaiting_budget_after_cheaper and intent not in (
            DialogueIntent.RESTART,
            DialogueIntent.LEAVE_LEAD,
            DialogueIntent.HANDOFF_MANAGER,
        ):
            bm, bx, _ = parse_budget_from_text(text)
            if bm is not None:
                context.known_params.budget_min = bm
            if bx is not None:
                context.known_params.budget_max = bx
            if bm is not None or bx is not None:
                context.awaiting_budget_after_cheaper = False
                return self._with_history(
                    context,
                    self._rerun_recommendation(context, DialogueIntent.CHANGE_BUDGET),
                )
            return self._with_history(
                context,
                ResponseBuilder.plain(
                    "В каком бюджете теперь смотреть? Например: до 50 000 ₽ или 40-60к.",
                    goal=AssistantGoal.ASK_MISSING_PARAM,
                    intent=DialogueIntent.OBJECTION_PRICE,
                ),
            )

        if intent == DialogueIntent.RESTART:
            self._reset_session(context)
            return self._with_history(
                context,
                AssistantResponse(
                    text=(
                        "Начинаем заново. Я задам несколько коротких вопросов "
                        "или можно сразу написать параметры одной фразой."
                    ),
                    goal=AssistantGoal.ASK_MISSING_PARAM,
                    intent=intent,
                    reset_context=True,
                ),
            )

        if context.lead_flow_active and intent != DialogueIntent.RESTART:
            return self._with_history(context, self._handle_lead_flow(text, context))

        if intent in (DialogueIntent.LEAVE_LEAD, DialogueIntent.HANDOFF_MANAGER):
            return self._with_history(context, self._start_lead_flow(context))

        if intent in (DialogueIntent.FAQ, DialogueIntent.DELIVERY_WARRANTY_MATERIALS):
            if self._is_motor_faq(text):
                return self._with_history(
                    context,
                    ResponseBuilder.faq(
                        answer=self._motor_faq_answer(context),
                        known_params=self._known_params_for_text(context),
                        cta="Сравнить варианты",
                        intent=DialogueIntent.FAQ,
                    ),
                )
            answer = self.faq_service.answer(text)
            if answer:
                return self._with_history(
                    context,
                    ResponseBuilder.faq(
                        answer=answer,
                        known_params=self._known_params_for_text(context),
                        cta="Подобрать стол",
                        intent=intent,
                    ),
                )
            return self._with_history(
                context,
                ResponseBuilder.no_exact_match(
                    blocking_constraint="в базе знаний нет точной статьи по этому вопросу",
                    alternatives=[
                        "Подобрать ближайшие модели и объяснить разницу",
                        "Передать вопрос менеджеру для точного ответа по срокам/условиям",
                    ],
                    intent=intent,
                    cta="Позвать менеджера",
                ),
            )

        if intent == DialogueIntent.COMPARE:
            return self._with_history(context, self._build_compare_response(context, intent))

        if intent == DialogueIntent.CLARIFY_RECOMMENDATION:
            if not context.recommended_products:
                return self._with_history(
                    context,
                    ResponseBuilder.plain(
                        "Сначала подберу 2–3 модели — и объясню, почему они подходят.",
                        goal=AssistantGoal.ASK_MISSING_PARAM,
                        intent=intent,
                    ),
                )
            return self._with_history(
                context,
                ResponseBuilder.with_cta(
                    "Я советую эти варианты по сочетанию цены, устойчивости, грузоподъёмности "
                    "и размера столешницы под ваш сценарий. Если хотите, сравню их по пунктам "
                    "или подберу альтернативу.",
                    goal=AssistantGoal.ANSWER_QUESTION,
                    intent=intent,
                    cta="Сравнить варианты",
                ),
            )

        if intent == DialogueIntent.CHANGE_BUDGET:
            bm, bx, _ = parse_budget_from_text(text)
            if bm is not None:
                context.known_params.budget_min = bm
            if bx is not None:
                context.known_params.budget_max = bx
            return self._with_history(context, self._rerun_recommendation(context, intent))

        if intent == DialogueIntent.CHANGE_SCENARIO:
            sc = parse_internal_scenario(text)
            if sc:
                context.known_params.use_case = sc
            if context.recommended_products:
                return self._with_history(context, self._rerun_recommendation(context, intent))
            return self._with_history(
                context,
                ResponseBuilder.plain(
                    f"Принял сценарий: {scenario_label_ru(context.known_params.use_case)}. "
                    "Продолжим подбор.",
                    goal=AssistantGoal.ASK_MISSING_PARAM,
                    intent=intent,
                ),
            )

        if intent == DialogueIntent.CHANGE_SIZE:
            sig = parse_signals(text, active_step=ACTIVE_STEP_SIZE)
            self._merge_signals_into_params(context, sig, text)
            if context.recommended_products:
                return self._with_history(context, self._rerun_recommendation(context, intent))

        if intent == DialogueIntent.MORE_PREMIUM:
            if not context.recommended_products:
                return self._with_history(
                    context,
                    ResponseBuilder.plain(
                        "Сначала подберу базовые варианты, затем сможем поднять планку по классу.",
                        goal=AssistantGoal.ASK_MISSING_PARAM,
                        intent=intent,
                    ),
                )
            prev = self.recommendation_service.get_products_by_ids(context.recommended_products)
            prices = [p.price for p in prev if p.price > 0]
            floor = max(prices) + 1 if prices else 50_000
            context.known_params.budget_min = floor
            context.known_params.budget_max = None
            q = self._build_recommendation_query(context)
            q.min_price_override = floor
            q.budget_max_rub = None
            q.budget = None
            ranked = self.recommendation_service.get_ranked_recommendations(q)
            if ranked:
                context.recommended_products = [item.product.id for item in ranked]
                explanations = self.explanation_service.explain_products(
                    [item.product for item in ranked],
                    query_context=self._sanitize_query_context(q),
                )
                intro = "Подобрал варианты дороже — с упором на запас по качеству и нагрузке."
                txt = intro + "\n\n" + self._format_main_recommendation_text(
                    context, ranked, explanations
                )
                return self._with_history(
                    context,
                    ResponseBuilder.with_cta(
                        txt,
                        goal=AssistantGoal.RECOMMEND,
                        intent=intent,
                        cta="Сравнить варианты",
                    ),
                )

        if intent == DialogueIntent.ACCESSORY_REQUEST:
            products = self.recommendation_service.repository.load_products()
            accessories = [
                product
                for product in products
                if product.in_stock and self._is_accessory(product.category)
            ]
            tags = catalog_tags_for_scenario(context.known_params.use_case)
            if tags:
                filtered = [p for p in accessories if tags.intersection(p.use_cases)]
                if filtered:
                    accessories = filtered
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
                    "Я помогу выбрать регулируемый стол под вашу задачу. "
                    "Можно ответить на короткие вопросы или написать всё одной фразой.",
                    goal=AssistantGoal.ASK_MISSING_PARAM,
                    intent=intent,
                    cta="Подобрать стол",
                ),
            )

        if intent == DialogueIntent.OBJECTION_PRICE:
            return self._with_history(
                context, self._build_cheaper_response(context, intent, text)
            )

        if (
            context.guide_active
            and not context.recommended_products
            and intent
            not in (
                DialogueIntent.FAQ,
                DialogueIntent.COMPARE,
                DialogueIntent.CLARIFY_RECOMMENDATION,
            )
        ):
            missing_col = _first_missing_collection_step(context.known_params)
            if missing_col is not None:
                if (
                    missing_before == missing_col
                    and not self._is_step_value_recognized(missing_col, context)
                    and text.strip()
                ):
                    return self._with_history(
                        context,
                        ResponseBuilder.plain(
                            self._invalid_step_hint(missing_col),
                            goal=AssistantGoal.ASK_MISSING_PARAM,
                            intent=intent,
                        ),
                    )
                prompt = self._next_collection_prompt(context)
                if prompt:
                    return self._with_history(
                        context,
                        ResponseBuilder.plain(
                            prompt,
                            goal=AssistantGoal.ASK_MISSING_PARAM,
                            intent=intent,
                        ),
                    )

            kp = context.known_params
            if (
                (kp.budget_max is not None or kp.budget_min is not None)
                and kp.budget_max is not None
                and kp.budget_max < 15_000
                and not context.low_budget_warned
                and not kp.budget_unspecified
            ):
                context.low_budget_warned = True
                return self._with_history(
                    context,
                    ResponseBuilder.plain(
                        "Уточните, пожалуйста: такая сумма редко хватает "
                        "на новый регулируемый стол в демо-каталоге. "
                        "Имелось в виду, например, до 50 000 ₽ или другая величина?",
                        goal=AssistantGoal.ASK_MISSING_PARAM,
                        intent=intent,
                    ),
                )

        if intent in (
            DialogueIntent.RECOMMEND,
            DialogueIntent.UNKNOWN,
            DialogueIntent.CLARIFY_RECOMMENDATION,
        ):
            missing = self._missing_legacy_budget_height(context)
            if (
                missing
                and intent in (DialogueIntent.RECOMMEND, DialogueIntent.UNKNOWN)
                and not context.recommended_products
                and not context.guide_active
            ):
                return self._with_history(
                    context,
                    ResponseBuilder.plain(
                        self._build_missing_params_prompt(missing),
                        goal=AssistantGoal.ASK_MISSING_PARAM,
                        intent=intent,
                    ),
                )

            collection_done = _first_missing_collection_step(context.known_params) is None
            if collection_done or not context.guide_active:
                rec = self._run_recommendation_block(context, intent)
                if rec.goal == AssistantGoal.RECOMMEND:
                    return self._with_history(context, rec)
                return self._with_history(context, rec)

            prompt = self._next_collection_prompt(context)
            if prompt:
                return self._with_history(
                    context,
                    ResponseBuilder.plain(
                        prompt,
                        goal=AssistantGoal.ASK_MISSING_PARAM,
                        intent=intent,
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
