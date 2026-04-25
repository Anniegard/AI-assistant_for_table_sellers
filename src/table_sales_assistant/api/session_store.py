from dataclasses import dataclass, field
from uuid import uuid4

from table_sales_assistant.assistant.models import DialogueContext, KnownClientParams


@dataclass(slots=True)
class WebSession:
    session_id: str
    context: DialogueContext
    last_recommendation_context: dict[str, object] = field(default_factory=dict)


class InMemoryWebSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, WebSession] = {}

    def create(self) -> WebSession:
        session_id = f"web-{uuid4()}"
        context = DialogueContext(user_id=len(self._sessions) + 1, known_params=KnownClientParams())
        session = WebSession(session_id=session_id, context=context)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> WebSession | None:
        return self._sessions.get(session_id)
