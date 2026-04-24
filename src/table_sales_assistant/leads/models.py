from pydantic import BaseModel, Field


class Lead(BaseModel):
    id: str
    created_at: str
    name: str
    phone: str
    city: str
    height_cm: int | None = Field(default=None, ge=0)
    budget: int | None = Field(default=None, ge=0)
    use_case: str | None = None
    monitors_count: int | None = Field(default=None, ge=0)
    has_pc_case: bool | None = None
    preferred_size: str | None = None
    needs_delivery: bool | None = None
    needs_assembly: bool | None = None
    recommended_products: list[str] = Field(default_factory=list)
    recent_questions: list[str] = Field(default_factory=list)
    selected_product_id: str | None = None
    assistant_comment: str | None = None
    comment: str | None = None
    source: str = 'telegram'
