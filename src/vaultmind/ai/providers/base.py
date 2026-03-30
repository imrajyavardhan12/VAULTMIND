"""Provider protocol — the abstract interface all AI providers implement."""

from __future__ import annotations

from typing import Protocol


class Provider(Protocol):
    """Abstract interface for AI providers.

    ~100 lines of abstraction instead of LiteLLM's 100+ provider support.
    We only need what we use.
    """

    model: str

    async def complete(self, prompt: str, system: str = "") -> str:
        """Send a prompt and return the completion text."""
        ...
