"""Tests for AI providers."""

from vaultmind.ai.providers import get_provider


def test_get_anthropic_provider(test_config):
    provider = get_provider(test_config, tier="fast")
    assert provider.model == "claude-sonnet-4-20250514"


def test_get_deep_provider(test_config):
    provider = get_provider(test_config, tier="deep")
    assert provider.model == "claude-opus-4-5"
