"""AI provider registry."""

from __future__ import annotations

from vaultmind.ai.providers.base import Provider
from vaultmind.config import AppConfig


def get_provider(config: AppConfig, tier: str = "fast") -> Provider:
    """Get the appropriate AI provider based on config.

    Tries providers in fallback_chain order until one is available.
    """
    from vaultmind.ai.providers.anthropic import AnthropicProvider
    from vaultmind.ai.providers.openai import OpenAIProvider

    provider_map: dict[str, type[Provider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
    }

    for provider_name in config.ai.fallback_chain:
        if provider_name not in provider_map:
            continue

        provider_config = config.ai.providers.get(provider_name)
        if provider_config is None:
            continue

        # Check if we have the required API key
        if provider_name == "anthropic" and not config.env.anthropic_api_key:
            continue
        if provider_name == "openai" and not config.env.openai_api_key:
            continue

        model = getattr(provider_config.models, tier, provider_config.models.fast)

        return provider_map[provider_name](
            api_key=getattr(config.env, f"{provider_name}_api_key", ""),
            model=model,
            max_tokens=config.ai.max_tokens,
        )

    from vaultmind.utils.display import print_error

    print_error(
        "No AI provider available.\n"
        "Set ANTHROPIC_API_KEY in your .env file and configure a provider in config.yaml."
    )
    raise SystemExit(1)
