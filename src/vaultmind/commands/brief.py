"""vm brief — weekly digest command."""

from __future__ import annotations

import asyncio

import typer
from rich.panel import Panel
from rich.table import Table

from vaultmind.ai.knowledge import WeeklyBrief, generate_weekly_brief
from vaultmind.ai.providers import get_provider
from vaultmind.config import load_config
from vaultmind.core.vault_index import filter_notes_by_days, scan_vault_notes
from vaultmind.utils.display import console, print_info, print_warning
from vaultmind.utils.logging import setup_logging


def brief(days: int = 7, limit: int = 20, verbose: bool = False) -> None:
    """Generate a weekly digest from recently saved notes."""
    setup_logging(verbose=verbose)
    config = load_config()
    notes = scan_vault_notes(config, only_vaultmind=True)
    filtered = filter_notes_by_days(notes, days=days)

    if not filtered:
        print_warning(f"No notes found in the last {days} days.")
        return

    selected = filtered[:limit]
    provider = get_provider(config, tier="fast")
    period_label = f"Last {days} days"

    report = asyncio.run(generate_weekly_brief(selected, provider, period_label=period_label))
    render_weekly_brief(report)


def render_weekly_brief(report: WeeklyBrief) -> None:
    """Render weekly digest output with rich components."""
    console.print(
        Panel(
            report.one_sentence_takeaway,
            title=f"🗓️ Weekly Brief — {report.period_label}",
            border_style="green",
        )
    )

    if report.themes:
        themes = Table(title="Themes")
        themes.add_column("Theme")
        themes.add_column("Insight")
        for item in report.themes:
            themes.add_row(item.name, item.insight)
        console.print(themes)
    else:
        print_info("No themes found.")

    if report.highlights:
        highlights = Table(title="Highlights")
        highlights.add_column("Title")
        highlights.add_column("Path")
        highlights.add_column("Reason")
        for note in report.highlights:
            highlights.add_row(note.title, note.path, note.reason)
        console.print(highlights)
    else:
        print_info("No highlights found.")

    gaps = "\n".join(f"- {gap}" for gap in report.gaps) if report.gaps else "- None"
    next_steps = (
        "\n".join(f"- {step}" for step in report.suggested_next_steps)
        if report.suggested_next_steps
        else "- None"
    )
    console.print(
        Panel(
            f"**Gaps**\n{gaps}\n\n**Suggested Next Steps**\n{next_steps}",
            title="Actionables",
            border_style="cyan",
        )
    )


if __name__ == "__main__":
    typer.run(brief)
