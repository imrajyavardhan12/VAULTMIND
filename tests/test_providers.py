"""Tests for AI providers."""

import asyncio

import httpx

from vaultmind.ai.providers import get_provider
from vaultmind.ai.providers.ollama import OllamaProvider
from vaultmind.config import AIConfig, AppConfig, EnvSettings, ProviderConfig, ProviderModels


def test_get_anthropic_provider(test_config):
    provider = get_provider(test_config, tier="fast")
    assert provider.model == "claude-sonnet-4-20250514"


def test_get_deep_provider(test_config):
    provider = get_provider(test_config, tier="deep")
    assert provider.model == "claude-opus-4-5"


def test_get_ollama_provider_without_api_key(tmp_vault):
    config = AppConfig(
        vault_path=tmp_vault,
        ai=AIConfig(
            default_provider="ollama",
            fallback_chain=["ollama"],
            providers={
                "ollama": ProviderConfig(
                    base_url="http://localhost:11434",
                    models=ProviderModels(fast="llama3", deep="llama3:70b"),
                )
            },
        ),
        env=EnvSettings(anthropic_api_key="", openai_api_key=""),
    )

    provider = get_provider(config, tier="deep")

    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama3:70b"


def test_ollama_provider_complete_uses_native_chat_endpoint():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        payload = httpx.Response(200, json={"message": {"content": "local answer"}})
        return payload

    transport = httpx.MockTransport(handler)
    provider = OllamaProvider(
        base_url="http://ollama.test",
        model="llama3",
        max_tokens=123,
        transport=transport,
    )

    result = asyncio.run(provider.complete("hello", system="system"))

    assert result == "local answer"
