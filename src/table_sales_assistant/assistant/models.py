from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class DialogueIntent(StrEnum):
    RECOMMEND = "recommend"
    FAQ = "faq"
    COMPARE = "compare"
    CLARIFY_RECOMMENDATION = "clarify_recommendation"
    LEAVE_LEAD = "leave_lead"
    HANDOFF_MANAGER = "handoff_manager"
    RESTART = "restart"
    DELIVERY_WARRANTY_MATERIALS = "delivery_warranty_materials"
    SMALL_TALK = "small_talk"
    OBJECTION_PRICE = "objection_price"
    ACCESSORY_REQUEST = "accessory_request"
    UNKNOWN = "unknown"


class AssistantGoal(StrEnum):
    ASK_MISSING_PARAM = "ask_missing_param"
    ANSWER_QUESTION = "answer_question"
    RECOMMEND = "recommend"
    COMPARE = "compare"
    HANDLE_OBJECTION = "handle_objection"
    COLLECT_LEAD = "collect_lead"
    HANDOFF_READY = "handoff_ready"


@dataclass(slots=True)
class KnownClientParams:
    height_cm: int | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    use_case: str | None = None
    monitors_count: int | None = None
    has_pc_case: bool | None = None
    preferred_size: str | None = None
    city: str | None = None
    needs_assembly: bool | None = None


@dataclass(slots=True)
class RecommendationCandidate:
    product_id: str
    fit_score: float
    reasons: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)
    best_for: str = ""


@dataclass(slots=True)
class DialogueContext:
    user_id: int
    dialogue_goal: str | None = None
    known_params: KnownClientParams = field(default_factory=KnownClientParams)
    recommended_products: list[str] = field(default_factory=list)
    recent_questions: list[str] = field(default_factory=list)
    recent_messages: list["DialogueMessage"] = field(default_factory=list)
    lead_readiness: int = 0
    manager_summary: str = ""

    def _add_message(self, role: str, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        self.recent_messages.append(
            DialogueMessage(
                role=role,
                text=cleaned,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )
        self.recent_messages = self.recent_messages[-10:]

    def add_user_message(self, text: str) -> None:
        self._add_message("user", text)

    def add_assistant_message(self, text: str) -> None:
        self._add_message("assistant", text)

    def get_recent_history(self, limit: int = 6) -> list["DialogueMessage"]:
        return self.recent_messages[-limit:]

    def get_context_summary(self) -> dict[str, object]:
        known_params = asdict(self.known_params)
        recent_questions = self.recent_questions[-5:]
        last_products = self.recommended_products[-3:]
        summary_parts = [
            "Консультация в Telegram по регулируемым столам.",
            f"Этап: {self.dialogue_goal or 'active_dialogue'}.",
            f"Параметры: {known_params}.",
            f"Последние вопросы: {recent_questions if recent_questions else '-'}.",
            f"Последние рекомендации: {last_products if last_products else '-'}.",
        ]
        return {
            "known_params": known_params,
            "recent_questions": recent_questions,
            "recommended_products": last_products,
            "dialogue_stage": self.dialogue_goal or "active_dialogue",
            "recent_dialogue_summary": " ".join(summary_parts),
        }


@dataclass(slots=True)
class DialogueMessage:
    role: str
    text: str
    timestamp: str


@dataclass(slots=True)
class AssistantPersona:
    name: str
    role: str
    style: str
    objective: str
    limitations: list[str]


@dataclass(slots=True)
class AssistantResponse:
    text: str
    goal: AssistantGoal
    intent: DialogueIntent
    cta: str | None = None
    start_lead_flow: bool = False
    reset_context: bool = False
