from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    category: str
    segment: str
    price: int = Field(ge=0)
    min_height_cm: int
    max_height_cm: int
    tabletop_width_cm: int
    tabletop_depth_cm: int
    motors_count: int = Field(ge=1)
    lifting_capacity_kg: int = Field(ge=0)
    material: str
    colors: list[str]
    use_cases: list[str]
    recommended_user_height_min_cm: int
    recommended_user_height_max_cm: int
    product_url: str
    in_stock: bool
    short_description: str
