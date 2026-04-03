"""vm init — interactive setup wizard for new users."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import typer
import yaml

from vaultmind.utils.display import console, print_error, print_success, print_warning

CONFIG_DIR = Path.home() / ".config" / "vaultmind"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
ENV_PATH = CONFIG_DIR / ".env"

VAULT_FOLDERS = [
    "📥 Inbox",
    "📚 Sources",
    "📚 Sources/AI",
    "📚 Sources/Tech",
    "📚 Sources/Philosophy",
    "📚 Sources/Business",
    "📚 Sources/Science",
    "📚 Sources/Design",
    "📚 Sources/Misc",
    "🛠️ Tools",
    "🐦 Threads",
    "💬 Discussions",
    "🃏 Flashcards",
    "📊 Digests",
    "📊 Digests/Weekly",
    "📊 Digests/Monthly",
    "🗺️ MOCs",
    "💡 Ideas",
    "⚙️ Meta",
]


def init(verbose: bool = False) -> None:
    """Set up VaultMind — creates config and connects your vault + API key."""
    console.print("\n[bold cyan]🧠 VaultMind Setup[/bold cyan]\n")

    # Check for existing config
    if CONFIG_PATH.exists():
        overwrite = typer.confirm(
            f"Config already exists at {CONFIG_PATH}. Overwrite?", default=False
        )
        if not overwrite:
            console.print("[dim]Setup cancelled.[/dim]")
            return

    # 1. Vault path
    vault_path = _ask_vault_path()

    # 2. AI provider
    provider, api_key = _ask_provider()

    # 3. Create vault folders
    _create_vault_folders(vault_path)

    # 4. Write config.yaml
    _write_config(vault_path, provider)

    # 5. Write .env
    _write_env(provider, api_key)

    console.print()
    print_success(
        "VaultMind is ready!",
        f"Config: {CONFIG_PATH}\n"
        f"Secrets: {ENV_PATH}\n"
        f"Vault: {vault_path}\n\n"
        f"Try it out:\n"
        f"  vm save https://github.com/astral-sh/uv",
    )


def _ask_vault_path() -> Path:
    """Prompt for Obsidian vault path and validate it."""
    while True:
        raw = typer.prompt(
            "📁 Obsidian vault path",
            default=str(Path.home() / "Obsidian Vault"),
        )
        vault_path = Path(raw).expanduser().resolve()

        if vault_path.exists() and vault_path.is_dir():
            console.print(f"  [green]✓[/green] Found vault at {vault_path}")
            return vault_path

        create = typer.confirm(
            f"  Directory doesn't exist. Create {vault_path}?", default=True
        )
        if create:
            vault_path.mkdir(parents=True, exist_ok=True)
            console.print(f"  [green]✓[/green] Created {vault_path}")
            return vault_path

        console.print("  [yellow]Try again.[/yellow]")


def _ask_provider() -> tuple[str, str]:
    """Prompt for AI provider choice and API key."""
    console.print("\n[bold]🤖 AI Provider[/bold]")
    console.print("  1. OpenAI  (gpt-4.1)")
    console.print("  2. Anthropic (claude-sonnet)")
    console.print("  3. Ollama  (local, no key needed)\n")

    choice = typer.prompt("Choose provider [1/2/3]", default="1")
    provider_map = {"1": "openai", "2": "anthropic", "3": "ollama"}
    provider = provider_map.get(choice, "openai")

    if provider == "ollama":
        console.print(f"  [green]✓[/green] Selected Ollama (no API key needed)")
        return provider, ""

    key_name = "OpenAI" if provider == "openai" else "Anthropic"
    console.print(f"\n  Get your key from:")
    if provider == "openai":
        console.print("  [dim]https://platform.openai.com/api-keys[/dim]")
    else:
        console.print("  [dim]https://console.anthropic.com/[/dim]")

    api_key = typer.prompt(f"\n🔑 {key_name} API key", hide_input=True)

    if not api_key.strip():
        print_warning("No API key provided. You can add it later in ~/.config/vaultmind/.env")
        return provider, ""

    console.print(f"  [green]✓[/green] API key saved")
    return provider, api_key.strip()


def _create_vault_folders(vault_path: Path) -> None:
    """Create the standard VaultMind folder structure in the vault."""
    created = 0
    for folder_name in VAULT_FOLDERS:
        folder = vault_path / folder_name
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            created += 1

    if created > 0:
        console.print(f"  [green]✓[/green] Created {created} vault folders")
    else:
        console.print(f"  [dim]Vault folders already exist[/dim]")


def _write_config(vault_path: Path, provider: str) -> None:
    """Write config.yaml to ~/.config/vaultmind/."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    fallback = [provider]
    for p in ["openai", "anthropic", "ollama"]:
        if p != provider:
            fallback.append(p)

    config_data = {
        "vault_path": str(vault_path),
        "folders": {
            "inbox": "📥 Inbox",
            "articles": "📚 Sources",
            "tools": "🛠️ Tools",
            "threads": "🐦 Threads",
            "discussions": "💬 Discussions",
            "flashcards": "🃏 Flashcards",
            "digests": "📊 Digests",
            "mocs": "🗺️ MOCs",
            "ideas": "💡 Ideas",
            "meta": "⚙️ Meta",
        },
        "ai": {
            "default_provider": provider,
            "fallback_chain": fallback,
            "max_tokens": 2000,
            "generate_flashcards": True,
            "generate_counterarguments": True,
            "rating": True,
            "providers": {
                "anthropic": {
                    "models": {"fast": "claude-sonnet-4-20250514", "deep": "claude-opus-4-5"},
                },
                "openai": {
                    "models": {"fast": "gpt-4.1-mini", "deep": "gpt-4.1"},
                },
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "models": {"fast": "llama3", "deep": "llama3"},
                },
            },
        },
        "preferences": {
            "default_status": "processed",
            "open_after_save": False,
            "notify_on_save": True,
        },
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    console.print(f"  [green]✓[/green] Config written to {CONFIG_PATH}")


def _write_env(provider: str, api_key: str) -> None:
    """Write .env with API key to ~/.config/vaultmind/ with restricted permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    lines = ["# VaultMind secrets — do not share or commit this file"]

    if provider == "anthropic":
        lines.append(f"ANTHROPIC_API_KEY={api_key}" if api_key else "ANTHROPIC_API_KEY=")
        lines.append("# OPENAI_API_KEY=")
    elif provider == "openai":
        lines.append("# ANTHROPIC_API_KEY=")
        lines.append(f"OPENAI_API_KEY={api_key}" if api_key else "OPENAI_API_KEY=")
    else:
        lines.append("# ANTHROPIC_API_KEY=")
        lines.append("# OPENAI_API_KEY=")

    lines.append("# GITHUB_TOKEN=")
    lines.append("")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Restrict permissions — only owner can read/write
    os.chmod(ENV_PATH, stat.S_IRUSR | stat.S_IWUSR)

    console.print(f"  [green]✓[/green] Secrets written to {ENV_PATH} (permissions: 600)")
