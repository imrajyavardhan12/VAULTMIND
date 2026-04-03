"""vm digest — topic synthesis command."""

from __future__ import annotations

import asyncio

import typer
from rich.panel import Panel
from rich.table import Table

from vaultmind.ai.knowledge import TopicDigest, generate_topic_digest
from vaultmind.ai.providers import get_provider
from vaultmind.config import load_config
from vaultmind.core.moc import should_generate_moc, write_moc
from vaultmind.core.search import SearchMatch, search_notes
from vaultmind.core.vault_index import scan_vault_notes
from vaultmind.utils.display import console, print_success, print_warning
from vaultmind.utils.logging import setup_logging


def digest(topic: str, limit: int = 15, no_moc: bool = False, verbose: bool = False) -> None:
    """Generate a synthesis digest for a topic across saved notes."""
    setup_logging(verbose=verbose)
    config = load_config()
    notes = scan_vault_notes(config, only_vaultmind=True)

    if not notes:
        print_warning("No VaultMind notes found to synthesize.")
        return

    matches = search_notes(notes, topic, limit=max(limit, 50))
    if not matches:
        print_warning(f'No notes matched topic: "{topic}"')
        return

    selected = matches[:limit]
    provider = get_provider(config, tier="deep")
    report = asyncio.run(generate_topic_digest(topic, selected, provider))
    render_topic_digest(report, selected)

    if not no_moc and should_generate_moc(topic, selected):
        path = write_moc(topic, report, selected, config)
        print_success("MOC Generated", f"Wrote topic MOC to:\n{path}")


def render_topic_digest(report: TopicDigest, matches: list[SearchMatch]) -> None:
    """Render digest output with rich panels/tables."""
    console.print(Panel(report.thesis, title=f"📚 Topic Digest — {report.topic}", border_style="blue"))

    if report.patterns:
        pattern_table = Table(title="Patterns")
        pattern_table.add_column("Pattern")
        for pattern in report.patterns:
            pattern_table.add_row(pattern)
        console.print(pattern_table)

    if report.tensions:
        tension_table = Table(title="Tensions")
        tension_table.add_column("Tension")
        for tension in report.tensions:
            tension_table.add_row(tension)
        console.print(tension_table)

    standout_table = Table(title="Standout Notes")
    standout_table.add_column("Title")
    standout_table.add_column("Path")
    standout_table.add_column("Reason")
    if report.standout_notes:
        for note in report.standout_notes:
            standout_table.add_row(note.title, note.path, note.reason)
    else:
        for match in matches[:3]:
            standout_table.add_row(match.note.title, match.note.relative_path, "High relevance")
    console.print(standout_table)

    questions = "\n".join(f"- {q}" for q in report.open_questions) if report.open_questions else "- None"
    console.print(Panel(questions, title="Open Questions", border_style="magenta"))


if __name__ == "__main__":
    typer.run(digest)
