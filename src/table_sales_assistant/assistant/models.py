from dataclasses import dataclass, field
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
    lead_readiness: int = 0
    manager_summary: str = ""


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
