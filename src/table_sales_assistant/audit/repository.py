from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from table_sales_assistant.audit.models import DialogueAuditEvent


class JSONLDialogueAuditRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, event: DialogueAuditEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(event.model_dump_json(ensure_ascii=False) + "\n")

    def read_recent(self, limit: int = 100) -> list[DialogueAuditEvent]:
        if limit <= 0 or not self.path.exists():
            return []
        recent_lines: deque[str] = deque(maxlen=limit)
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                cleaned = line.strip()
                if cleaned:
                    recent_lines.append(cleaned)

        events: list[DialogueAuditEvent] = []
        for line in recent_lines:
            payload = json.loads(line)
            events.append(DialogueAuditEvent.model_validate(payload))
        return events

    def export_events_as_json(self) -> list[dict]:
        if not self.path.exists():
            return []
        exported: list[dict] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                cleaned = line.strip()
                if not cleaned:
                    continue
                exported.append(json.loads(cleaned))
        return exported

