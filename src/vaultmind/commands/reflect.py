"""vm reflect — weekly mirror command."""

from __future__ import annotations

import asyncio

import typer
from rich.panel import Panel
from rich.table import Table

from vaultmind.ai.knowledge import ReflectionReport, generate_reflection
from vaultmind.ai.providers import get_provider
from vaultmind.config import load_config
from vaultmind.core.vault_index import VaultNoteRecord, filter_notes_by_days, scan_vault_notes
from vaultmind.utils.display import console, print_warning
from vaultmind.utils.logging import setup_logging


def reflect(days: int = 7, limit: int = 20, verbose: bool = False) -> None:
    """Generate a reflection report for recent notes."""
    setup_logging(verbose=verbose)
    config = load_config()
    notes = scan_vault_notes(config, only_vaultmind=True)
    filtered = filter_notes_by_days(notes, days=days)

    if not filtered:
        print_warning(f"No notes found in the last {days} days.")
        return

    selected = filtered[:limit]
    provider = get_provider(config, tier="deep")
    report = asyncio.run(
        generate_reflection(selected, provider, period_label=f"Last {days} days")
    )
    render_reflection(report, supporting_notes=selected)


def render_reflection(report: ReflectionReport, *, supporting_notes: list[VaultNoteRecord]) -> None:
    """Render reflection output with rich panels/tables."""
    console.print(
        Panel(
            report.recommended_experiment,
            title=f"🪞 Reflection — {report.period_label}",
            border_style="blue",
        )
    )

    sections = [
        ("Dominant Themes", report.dominant_themes),
        ("Belief Shifts", report.belief_shifts),
        ("Tensions", report.tensions),
        ("Blindspots", report.blindspots),
        ("Questions For You", report.questions_for_you),
    ]
    for title, items in sections:
        table = Table(title=title)
        table.add_column("Item")
        for item in items:
            table.add_row(item)
        if not items:
            table.add_row("-")
        console.print(table)

    notes_table = Table(title="Supporting Notes")
    notes_table.add_column("Title")
    notes_table.add_column("Path")
    for note in supporting_notes[:10]:
        notes_table.add_row(note.title, note.relative_path)
    console.print(notes_table)


if __name__ == "__main__":
    typer.run(reflect)
