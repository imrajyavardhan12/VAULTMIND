"""CLI entry point — typer app."""

from __future__ import annotations

from typing import Optional

import typer

from vaultmind.utils.logging import setup_logging

app = typer.Typer(
    name="vm",
    help="VaultMind — Your personal AI-powered second brain.",
    add_completion=False,
    no_args_is_help=True,
)


@app.command()
def save(
    url: str = typer.Argument(help="URL to process and save"),
    tag: Optional[list[str]] = typer.Option(None, "--tag", "-t", help="Extra tags (repeatable)"),
    folder: Optional[str] = typer.Option(
        None, "--folder", "-f", help="Override folder routing (vault-relative)"
    ),
    force: bool = typer.Option(False, "--force", help="Re-process even if already saved"),
    no_flash: bool = typer.Option(False, "--no-flash", help="Skip flashcard generation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging"),
) -> None:
    """Process any URL and save a structured note to your Obsidian vault."""
    setup_logging(verbose=verbose)

    from vaultmind.commands.save import save_url
    from vaultmind.config import load_config

    config = load_config()
    save_url(url, config, tags=tag, folder=folder, force=force, no_flash=no_flash)


@app.command()
def version() -> None:
    """Show VaultMind version."""
    from vaultmind import __version__

    typer.echo(f"VaultMind v{__version__}")


if __name__ == "__main__":
    app()
