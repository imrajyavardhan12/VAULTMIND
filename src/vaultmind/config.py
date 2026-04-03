"""Pydantic settings — typed, validated config with env var support."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderModels(BaseModel):
    fast: str
    deep: str


class ProviderConfig(BaseModel):
    models: ProviderModels
    base_url: str | None = None


class AIConfig(BaseModel):
    default_provider: str = "anthropic"
    fallback_chain: list[str] = Field(default_factory=lambda: ["anthropic"])
    max_tokens: int = 2000
    generate_flashcards: bool = True
    generate_counterarguments: bool = True
    rating: bool = True
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)


class FolderConfig(BaseModel):
    inbox: str = "📥 Inbox"
    articles: str = "📚 Sources"
    tools: str = "🛠️ Tools"
    threads: str = "🐦 Threads"
    discussions: str = "💬 Discussions"
    flashcards: str = "🃏 Flashcards"
    digests: str = "📊 Digests"
    mocs: str = "🗺️ MOCs"
    ideas: str = "💡 Ideas"
    meta: str = "⚙️ Meta"


class PreferencesConfig(BaseModel):
    default_status: str = "processed"
    open_after_save: bool = False
    notify_on_save: bool = True


def _find_env_file() -> str:
    """Find .env in cwd or ~/.config/vaultmind/."""
    candidates = [
        Path.cwd() / ".env",
        Path.home() / ".config" / "vaultmind" / ".env",
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return ".env"


class EnvSettings(BaseSettings):
    """Secrets loaded from .env file."""

    model_config = SettingsConfigDict(env_file=_find_env_file(), env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    github_token: str = ""
    ollama_base_url: str = "http://localhost:11434"


class AppConfig(BaseModel):
    """Full application config — merged from config.yaml + .env."""

    vault_path: Path
    folders: FolderConfig = Field(default_factory=FolderConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    preferences: PreferencesConfig = Field(default_factory=PreferencesConfig)
    env: EnvSettings = Field(default_factory=EnvSettings)


def _find_config_file() -> Path | None:
    """Find config.yaml in project root or ~/.config/vaultmind/."""
    candidates = [
        Path.cwd() / "config.yaml",
        Path.home() / ".config" / "vaultmind" / "config.yaml",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def load_config() -> AppConfig:
    """Load config from config.yaml + .env with validation."""
    env = EnvSettings()

    config_path = _find_config_file()
    if config_path is None:
        from vaultmind.utils.display import print_error

        print_error(
            "VaultMind is not set up yet.\n"
            "Run the setup wizard:\n"
            "  vm init"
        )
        raise SystemExit(1)

    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    raw["env"] = env
    return AppConfig(**raw)
