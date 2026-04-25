from __future__ import annotations

import logging
import re
from typing import Any

from table_sales_assistant.audit.models import DialogueAuditEvent, DialogueMode
from table_sales_assistant.audit.repository import JSONLDialogueAuditRepository

logger = logging.getLogger(__name__)

_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{8,}\d)(?!\w)")
_EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")


def sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    sanitized = _EMAIL_RE.sub("[email]", value)
    sanitized = _PHONE_RE.sub("[phone]", sanitized)
    return sanitized


def detect_mode(
    *,
    provider: str | None = None,
    used_llm: bool | None = None,
) -> DialogueMode:
    provider_normalized = (provider or "").strip().lower()
    if provider_normalized in {"yandex", "yandex_ai", "yandexgpt"}:
        return "yandex_ai"
    if used_llm is True and provider_normalized in {"", "openai", "gpt"}:
        return "openai"
    if used_llm is False:
        return "offline"
    return "unknown"


class DialogueAuditService:
    def __init__(self, repository: JSONLDialogueAuditRepository, *, enabled: bool = True) -> None:
        self.repository = repository
        self.enabled = enabled

    def log_event(self, event: DialogueAuditEvent) -> None:
        if not self.enabled:
            return
        try:
            self.repository.append(event)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to append dialogue audit event: %s", exc)

    def create_event(self, **kwargs: Any) -> DialogueAuditEvent:
        payload = dict(kwargs)
        payload["user_message"] = sanitize_text(payload.get("user_message"))
        payload["assistant_response"] = sanitize_text(payload.get("assistant_response"))
        return DialogueAuditEvent(**payload)

    def read_recent(self, limit: int = 100) -> list[DialogueAuditEvent]:
        return self.repository.read_recent(limit=limit)

    def export_events_as_json(self) -> list[dict]:
        return self.repository.export_events_as_json()

