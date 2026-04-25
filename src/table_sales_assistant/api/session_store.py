from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic
from uuid import uuid4

from table_sales_assistant.assistant.models import DialogueContext, KnownClientParams


@dataclass(slots=True)
class WebSession:
    session_id: str
    context: DialogueContext
    expires_at: float
    last_recommendation_context: dict[str, object] = field(default_factory=dict)


class InMemoryWebSessionStore:
    def __init__(
        self,
        *,
        ttl_seconds: int = 60 * 30,
        now_fn: Callable[[], float] | None = None,
    ) -> None:
        self._sessions: dict[str, WebSession] = {}
        self._ttl_seconds = max(1, ttl_seconds)
        self._now_fn = now_fn or monotonic

    def _cleanup_expired(self) -> None:
        now = self._now_fn()
        expired_ids = [
            session_id for session_id, item in self._sessions.items() if item.expires_at <= now
        ]
        for session_id in expired_ids:
            self._sessions.pop(session_id, None)

    def create(self) -> WebSession:
        self._cleanup_expired()
        session_id = f"web-{uuid4()}"
        context = DialogueContext(user_id=len(self._sessions) + 1, known_params=KnownClientParams())
        session = WebSession(
            session_id=session_id,
            context=context,
            expires_at=self._now_fn() + self._ttl_seconds,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> WebSession | None:
        self._cleanup_expired()
        session = self._sessions.get(session_id)
        if session is None:
            return None
        session.expires_at = self._now_fn() + self._ttl_seconds
        return session
