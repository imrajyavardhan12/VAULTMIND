"""OpenAI/GPT provider."""

from __future__ import annotations

import structlog
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()


class OpenAIProvider:
    """OpenAI GPT provider using the official SDK."""

    def __init__(self, api_key: str, model: str, max_tokens: int = 2000) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self._client = AsyncOpenAI(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def complete(self, prompt: str, system: str = "") -> str:
        """Send a prompt to OpenAI and return the completion text."""
        log.info("openai_request", model=self.model)

        response = await self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        text = response.choices[0].message.content or ""
        log.info(
            "openai_response",
            model=self.model,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )
        return text
