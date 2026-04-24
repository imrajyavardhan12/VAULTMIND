"""Ollama provider using the local HTTP API."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()


class OllamaProvider:
    """Local Ollama provider.

    Uses Ollama's native `/api/chat` endpoint rather than an OpenAI-compatible
    shim, so local mode works without an API key.
    """

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        max_tokens: int = 2000,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self._transport = transport

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def complete(self, prompt: str, system: str = "") -> str:
        """Send a prompt to Ollama and return the completion text."""
        log.info("ollama_request", model=self.model, base_url=self.base_url)

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": self.max_tokens},
        }

        async with httpx.AsyncClient(transport=self._transport, timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)

        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return ""

        message = data.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                log.info("ollama_response", model=self.model)
                return content

        fallback = data.get("response")
        return fallback if isinstance(fallback, str) else ""
