from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    mode: str = "demo"


class CreateSessionResponse(BaseModel):
    session_id: str


class MessageRequest(BaseModel):
    session_id: str
    text: str = Field(min_length=1)


class ProductCard(BaseModel):
    id: str
    name: str
    price: int = Field(ge=0)
    product_url: str


class LeadState(BaseModel):
    start_lead_flow: bool = False
    has_recommendations: bool = False
    known_params: dict[str, object] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    session_id: str
    assistant_text: str
    intent: str
    quick_replies: list[str] = Field(default_factory=list)
    recommended_products: list[ProductCard] = Field(default_factory=list)
    lead_state: LeadState
    manager_summary: str | None = None


class LeadRequest(BaseModel):
    session_id: str
    name: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    city: str = Field(min_length=1)
    comment: str | None = None
    height_cm: int | None = Field(default=None, ge=0)
    budget: int | None = Field(default=None, ge=0)
    use_case: str | None = None
    monitors_count: int | None = Field(default=None, ge=0)
    has_pc_case: bool | None = None
    preferred_size: str | None = None
    needs_delivery: bool | None = None
    needs_assembly: bool | None = None


class LeadResponse(BaseModel):
    lead_id: str
    source: str
    manager_summary: str | None = None
