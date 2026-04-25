from datetime import UTC, datetime
from uuid import uuid4

from table_sales_assistant.leads.models import Lead


class LeadService:
    @staticmethod
    def parse_bool(raw_value: str) -> bool:
        value = raw_value.strip().lower()
        return value in {"да", "yes", "y", "true", "1"}

    @staticmethod
    def build_lead(data: dict[str, object], *, source: str = "telegram_demo") -> Lead:
        return Lead(
            id=f"lead-{uuid4()}",
            created_at=datetime.now(UTC).isoformat(),
            name=str(data["name"]),
            phone=str(data["phone"]),
            city=str(data["city"]),
            height_cm=int(data["height_cm"]) if data.get("height_cm") is not None else None,
            budget=int(data["budget"]) if data.get("budget") is not None else None,
            use_case=str(data["use_case"]) if data.get("use_case") else None,
            monitors_count=(
                int(data["monitors_count"])
                if data.get("monitors_count") is not None
                else None
            ),
            has_pc_case=(
                bool(data["has_pc_case"]) if data.get("has_pc_case") is not None else None
            ),
            preferred_size=str(data["preferred_size"]) if data.get("preferred_size") else None,
            needs_delivery=(
                bool(data["needs_delivery"])
                if data.get("needs_delivery") is not None
                else None
            ),
            needs_assembly=(
                bool(data["needs_assembly"])
                if data.get("needs_assembly") is not None
                else None
            ),
            known_params=dict(data.get("known_params", {})),
            recommended_products=list(data.get("recommended_products", [])),
            recent_dialogue_summary=(
                str(data["recent_dialogue_summary"])
                if data.get("recent_dialogue_summary")
                else None
            ),
            recent_questions=list(data.get("recent_questions", [])),
            selected_product_id=(
                str(data["selected_product_id"]) if data.get("selected_product_id") else None
            ),
            assistant_comment=(
                str(data["assistant_comment"]) if data.get("assistant_comment") else None
            ),
            comment=None if data.get("comment") in (None, "-", "") else str(data["comment"]),
            source=source,
        )
