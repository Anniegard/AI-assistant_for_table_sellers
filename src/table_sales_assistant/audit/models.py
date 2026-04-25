from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

DialogueMode = Literal["openai", "offline", "yandex_ai", "unknown"]
DialogueStatus = Literal["success", "error"]
DialogueEventType = Literal["user_message_received", "assistant_response_sent"]


class DialogueAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: DialogueEventType = "assistant_response_sent"
    conversation_id: str
    channel: str = "telegram"
    user_id: int | None = None
    username: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    mode: DialogueMode = "unknown"
    provider: str | None = None
    model: str | None = None
    intent: str | None = None
    status: DialogueStatus = "success"
    user_message: str | None = None
    assistant_response: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    latency_ms: int | None = None
    lead_id: str | None = None
    recommended_products: list[str] = Field(default_factory=list)
    prompt_version: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

