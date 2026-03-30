"""Anthropic/Claude provider."""

from __future__ import annotations

import anthropic
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()


class AnthropicProvider:
    """Anthropic Claude provider using the official SDK."""

    def __init__(self, api_key: str, model: str, max_tokens: int = 2000) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def complete(self, prompt: str, system: str = "") -> str:
        """Send a prompt to Claude and return the completion text."""
        log.info("anthropic_request", model=self.model)

        message = await self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system if system else "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text
        log.info(
            "anthropic_response",
            model=self.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
        return text
