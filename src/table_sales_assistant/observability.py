import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("table_sales_assistant.observability")
_JSON_LOG_PATH = Path("data/dialogue_events.jsonl")


def log_dialogue_event(
    *,
    phase: str,
    user_id: int | None = None,
    question: str | None = None,
    answer: str | None = None,
    lead_id: str | None = None,
    function_name: str | None = None,
    bot_id: int | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "phase": phase,
        "question": question,
        "answer": answer,
        "user_id": user_id,
        "lead_id": lead_id,
        "function_name": function_name,
        "bot_id": bot_id,
    }
    if extra:
        payload["extra"] = extra

    logger.info("dialogue_event %s", payload)
    try:
        _JSON_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _JSON_LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to persist dialogue json log: %s", exc)
