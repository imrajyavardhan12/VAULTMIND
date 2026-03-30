"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from vaultmind.config import (
    AIConfig,
    AppConfig,
    EnvSettings,
    FolderConfig,
    PreferencesConfig,
    ProviderConfig,
    ProviderModels,
)


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault directory structure."""
    folders = [
        "📥 Inbox",
        "📚 Sources/AI",
        "📚 Sources/Tech",
        "📚 Sources/Misc",
        "🛠️ Tools",
        "💬 Discussions",
        "🐦 Threads",
    ]
    for folder in folders:
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def test_config(tmp_vault: Path) -> AppConfig:
    """Create a test AppConfig pointing at a temp vault."""
    return AppConfig(
        vault_path=tmp_vault,
        folders=FolderConfig(),
        ai=AIConfig(
            default_provider="anthropic",
            fallback_chain=["anthropic"],
            providers={
                "anthropic": ProviderConfig(
                    models=ProviderModels(fast="claude-sonnet-4-20250514", deep="claude-opus-4-5")
                )
            },
        ),
        preferences=PreferencesConfig(),
        env=EnvSettings(anthropic_api_key="test-key"),
    )
