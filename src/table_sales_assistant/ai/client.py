import logging
from time import perf_counter

from openai import OpenAI

from table_sales_assistant.observability import log_dialogue_event

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str | None = None, *, enabled: bool = True) -> None:
        self.api_key = api_key or ""
        self.enabled = enabled
        self._client = OpenAI(api_key=self.api_key) if self.enabled and self.api_key else None

    @property
    def is_enabled(self) -> bool:
        return self.enabled and self._client is not None

    def simple_chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self._client:
            disabled_reason = (
                "OPENAI_ENABLED is false."
                if not self.enabled
                else "OPENAI_API_KEY is not configured."
            )
            log_dialogue_event(
                phase="openai_disabled",
                question=user_prompt,
                answer=f"AI mode is disabled: {disabled_reason}",
                function_name="OpenAIClient.simple_chat",
            )
            return ""
        started = perf_counter()
        log_dialogue_event(
            phase="openai_request",
            question=user_prompt,
            function_name="OpenAIClient.simple_chat",
            extra={"model": "gpt-4.1-mini", "system_prompt_len": len(system_prompt)},
        )
        try:
            response = self._client.responses.create(
                model="gpt-4.1-mini",
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            output_text = response.output_text
            elapsed_ms = int((perf_counter() - started) * 1000)
            logger.info("OpenAI response processed in %sms", elapsed_ms)
            log_dialogue_event(
                phase="openai_response",
                question=user_prompt,
                answer=output_text,
                function_name="OpenAIClient.simple_chat",
                extra={"model": "gpt-4.1-mini", "latency_ms": elapsed_ms},
            )
            return output_text
        except Exception as exc:
            elapsed_ms = int((perf_counter() - started) * 1000)
            logger.exception("OpenAI request failed in simple_chat after %sms", elapsed_ms)
            log_dialogue_event(
                phase="openai_error",
                question=user_prompt,
                function_name="OpenAIClient.simple_chat",
                extra={
                    "model": "gpt-4.1-mini",
                    "latency_ms": elapsed_ms,
                    "error_type": type(exc).__name__,
                },
            )
            return ""
