from openai import OpenAI


class OpenAIClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or ''
        self._client = OpenAI(api_key=self.api_key) if self.api_key else None

    @property
    def is_enabled(self) -> bool:
        return self._client is not None

    def simple_chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self._client:
            return 'AI mode is disabled: OPENAI_API_KEY is not configured.'
        response = self._client.responses.create(
            model='gpt-4.1-mini',
            input=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        )
        return response.output_text
