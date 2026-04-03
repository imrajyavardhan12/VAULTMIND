"""vm find — keyword and fuzzy search."""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table

from vaultmind.config import load_config
from vaultmind.core.search import SearchMatch, search_notes
from vaultmind.core.vault_index import scan_vault_notes
from vaultmind.utils.display import console, print_info, print_warning
from vaultmind.utils.logging import setup_logging


def find(query: str | None = None, limit: int = 50, verbose: bool = False) -> None:
    """Find notes by keyword/fuzzy query across the vault."""
    setup_logging(verbose=verbose)
    config = load_config()
    notes = scan_vault_notes(config, only_vaultmind=True)

    if not notes:
        print_warning("No VaultMind notes found.")
        return

    search_query = (query or "").strip()
    effective_limit = min(limit, 20) if not search_query else limit
    matches = search_notes(notes, search_query, limit=effective_limit)

    if not matches:
        print_info("No matches found.")
        return

    render_find_results(matches, query=search_query)


def render_find_results(matches: list[SearchMatch], *, query: str) -> None:
    """Render search results in table form."""
    title = f'🔎 Search Results — "{query}"' if query else "🔎 Search Results — Recent Notes"
    table = Table(title=title)
    table.add_column("Score", justify="right")
    table.add_column("Title")
    table.add_column("Tags")
    table.add_column("Saved")
    table.add_column("Path")

    for match in matches:
        saved = match.note.saved_at.date().isoformat() if match.note.saved_at else "-"
        tags = ", ".join(match.note.tags[:4]) if match.note.tags else "-"
        table.add_row(f"{match.score:.1f}", match.note.title, tags, saved, match.note.relative_path)

    console.print(table)

    first = matches[0]
    excerpt = first.excerpt or "No excerpt available."
    console.print(Panel(excerpt, title=f"Preview: {first.note.title}", border_style="cyan"))


if __name__ == "__main__":
    typer.run(find)
