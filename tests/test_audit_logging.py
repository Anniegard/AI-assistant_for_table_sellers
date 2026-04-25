import json
import logging
from pathlib import Path

from table_sales_assistant.audit.models import DialogueAuditEvent
from table_sales_assistant.audit.repository import JSONLDialogueAuditRepository
from table_sales_assistant.audit.service import DialogueAuditService, detect_mode, sanitize_text


def test_append_single_event_to_jsonl(tmp_path: Path) -> None:
    repository = JSONLDialogueAuditRepository(tmp_path / "audit.jsonl")
    service = DialogueAuditService(repository, enabled=True)

    event = service.create_event(
        conversation_id="telegram:1",
        channel="telegram",
        mode="offline",
        status="success",
        user_message="привет",
        assistant_response="здравствуйте",
    )
    service.log_event(event)

    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["conversation_id"] == "telegram:1"
    assert payload["status"] == "success"


def test_jsonl_lines_are_valid_json(tmp_path: Path) -> None:
    repository = JSONLDialogueAuditRepository(tmp_path / "events.jsonl")
    service = DialogueAuditService(repository, enabled=True)
    service.log_event(
        service.create_event(
            conversation_id="telegram:1",
            channel="telegram",
            mode="offline",
            status="success",
            user_message="test 1",
            assistant_response="ok 1",
        )
    )
    service.log_event(
        service.create_event(
            conversation_id="telegram:2",
            channel="telegram",
            mode="unknown",
            status="error",
            user_message="test 2",
            assistant_response="fallback",
            error_type="RuntimeError",
            error_message="boom",
        )
    )

    for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines():
        parsed = json.loads(line)
        assert isinstance(parsed, dict)
        assert "event_id" in parsed


def test_read_recent_limit_returns_last_items(tmp_path: Path) -> None:
    repository = JSONLDialogueAuditRepository(tmp_path / "recent.jsonl")
    service = DialogueAuditService(repository, enabled=True)
    for idx in range(5):
        service.log_event(
            service.create_event(
                conversation_id=f"telegram:{idx}",
                channel="telegram",
                mode="offline",
                status="success",
                user_message=f"q{idx}",
                assistant_response=f"a{idx}",
            )
        )

    recent = service.read_recent(limit=2)
    assert [event.conversation_id for event in recent] == ["telegram:3", "telegram:4"]


def test_export_events_as_json(tmp_path: Path) -> None:
    repository = JSONLDialogueAuditRepository(tmp_path / "export.jsonl")
    service = DialogueAuditService(repository, enabled=True)
    service.log_event(
        service.create_event(
            conversation_id="web-1",
            channel="web_api",
            mode="offline",
            status="success",
            user_message="рост 180 бюджет 70к",
            assistant_response="подобрал варианты",
        )
    )

    exported = service.export_events_as_json()
    assert len(exported) == 1
    assert exported[0]["channel"] == "web_api"


def test_sanitize_text_masks_phone_and_email() -> None:
    text = "Пиши на ivan@example.com или +7 (999) 123-45-67 по столу."
    sanitized = sanitize_text(text)
    assert sanitized is not None
    assert "[email]" in sanitized
    assert "[phone]" in sanitized
    assert "по столу" in sanitized


def test_write_error_does_not_crash_application(caplog) -> None:
    class BrokenRepository:
        def append(self, event: DialogueAuditEvent) -> None:
            raise OSError("disk full")

        def read_recent(self, limit: int = 100) -> list[DialogueAuditEvent]:
            return []

        def export_events_as_json(self) -> list[dict]:
            return []

    service = DialogueAuditService(BrokenRepository(), enabled=True)  # type: ignore[arg-type]
    event = service.create_event(
        conversation_id="telegram:1",
        channel="telegram",
        mode="offline",
        status="success",
        user_message="hello",
        assistant_response="ok",
    )

    with caplog.at_level(logging.WARNING):
        service.log_event(event)
    assert "Failed to append dialogue audit event" in caplog.text


def test_detect_mode_variants() -> None:
    assert detect_mode(provider="openai") == "openai"
    assert detect_mode(provider="yandex_ai") == "yandex_ai"
    assert detect_mode(openai_requested=True, openai_available=False) == "offline"
    assert detect_mode(openai_requested=False, openai_available=False) == "unknown"

