"""vm stats — vault health dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import typer
from rich.panel import Panel
from rich.table import Table

from vaultmind.config import AppConfig, load_config
from vaultmind.core.flashcards import extract_flashcards_from_body
from vaultmind.core.vault_index import VaultNoteRecord, scan_vault_notes
from vaultmind.utils.display import console, print_info
from vaultmind.utils.logging import setup_logging


@dataclass(slots=True)
class VaultStats:
    total_notes: int
    vaultmind_notes: int
    notes_this_week: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    top_tags: list[tuple[str, int]]
    avg_rating: float | None
    avg_read_time_minutes: float | None
    flashcard_coverage_pct: float
    tagless_note_paths: list[str]
    partial_or_review_paths: list[str]
    moc_candidates: list[tuple[str, int]]


def stats(verbose: bool = False) -> None:
    """Show vault health metrics and quality signals."""
    setup_logging(verbose=verbose)
    config = load_config()
    notes = scan_vault_notes(config, only_vaultmind=False)

    if not notes:
        print_info("No notes found in the vault yet.")
        return

    computed = compute_vault_stats(notes, config)
    render_stats_dashboard(computed)


def compute_vault_stats(notes: list[VaultNoteRecord], config: AppConfig) -> VaultStats:
    """Compute high-level and quality-oriented vault metrics."""
    del config  # reserved for future config-dependent metrics

    now = datetime.now(UTC)
    cutoff = now - timedelta(days=7)

    vaultmind_notes = [note for note in notes if note.vaultmind]
    notes_this_week = sum(1 for note in vaultmind_notes if note.saved_at and note.saved_at >= cutoff)

    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    tag_counts: dict[str, int] = {}
    ratings: list[int] = []
    read_times: list[int] = []
    tagless_note_paths: list[str] = []
    partial_or_review_paths: list[str] = []
    flashcard_notes = 0

    for note in notes:
        note_type = (note.source_type or "unknown").lower()
        by_type[note_type] = by_type.get(note_type, 0) + 1

        status = (note.status or "unknown").lower()
        by_status[status] = by_status.get(status, 0) + 1

        if note.vaultmind:
            if not note.tags:
                tagless_note_paths.append(note.relative_path)
            if status in {"partial", "review"}:
                partial_or_review_paths.append(note.relative_path)
            if extract_flashcards_from_body(note.body):
                flashcard_notes += 1

        for tag in note.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if note.rating is not None:
            ratings.append(note.rating)
        if note.read_time_minutes is not None:
            read_times.append(note.read_time_minutes)

    top_tags = sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:15]
    moc_candidates = [item for item in top_tags if item[1] >= 5]

    avg_rating = (sum(ratings) / len(ratings)) if ratings else None
    avg_read = (sum(read_times) / len(read_times)) if read_times else None

    coverage = 0.0
    if vaultmind_notes:
        coverage = (flashcard_notes / len(vaultmind_notes)) * 100

    return VaultStats(
        total_notes=len(notes),
        vaultmind_notes=len(vaultmind_notes),
        notes_this_week=notes_this_week,
        by_type=by_type,
        by_status=by_status,
        top_tags=top_tags,
        avg_rating=avg_rating,
        avg_read_time_minutes=avg_read,
        flashcard_coverage_pct=coverage,
        tagless_note_paths=sorted(tagless_note_paths),
        partial_or_review_paths=sorted(partial_or_review_paths),
        moc_candidates=moc_candidates,
    )


def render_stats_dashboard(stats: VaultStats) -> None:
    """Render a rich dashboard for vault stats."""
    summary_lines = [
        f"Total Notes: {stats.total_notes}",
        f"VaultMind Notes: {stats.vaultmind_notes}",
        f"Notes This Week: {stats.notes_this_week}",
        f"Avg Rating: {stats.avg_rating:.2f}" if stats.avg_rating is not None else "Avg Rating: n/a",
        (
            f"Avg Read Time: {stats.avg_read_time_minutes:.2f} min"
            if stats.avg_read_time_minutes is not None
            else "Avg Read Time: n/a"
        ),
        f"Flashcard Coverage: {stats.flashcard_coverage_pct:.1f}%",
    ]
    console.print(Panel("\n".join(summary_lines), title="📊 VaultMind Stats", border_style="cyan"))

    type_table = Table(title="By Type", show_header=True)
    type_table.add_column("Type")
    type_table.add_column("Count", justify="right")
    for key, value in sorted(stats.by_type.items(), key=lambda item: (-item[1], item[0])):
        type_table.add_row(key, str(value))
    console.print(type_table)

    status_table = Table(title="By Status", show_header=True)
    status_table.add_column("Status")
    status_table.add_column("Count", justify="right")
    for key, value in sorted(stats.by_status.items(), key=lambda item: (-item[1], item[0])):
        status_table.add_row(key, str(value))
    console.print(status_table)

    tags_table = Table(title="Top Tags", show_header=True)
    tags_table.add_column("Tag")
    tags_table.add_column("Count", justify="right")
    for tag, count in stats.top_tags:
        tags_table.add_row(tag, str(count))
    console.print(tags_table)

    if stats.moc_candidates:
        moc_table = Table(title="MOC Candidates (count >= 5)", show_header=True)
        moc_table.add_column("Tag")
        moc_table.add_column("Count", justify="right")
        for tag, count in stats.moc_candidates:
            moc_table.add_row(tag, str(count))
        console.print(moc_table)

    if stats.tagless_note_paths:
        console.print(Panel("\n".join(stats.tagless_note_paths[:20]), title="Tagless Notes", border_style="yellow"))

    if stats.partial_or_review_paths:
        console.print(
            Panel(
                "\n".join(stats.partial_or_review_paths[:20]),
                title="Partial/Review Notes",
                border_style="magenta",
            )
        )


if __name__ == "__main__":
    typer.run(stats)
