"""Tests for vm stats command helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vaultmind.commands.stats import compute_vault_stats
from vaultmind.core.vault_index import VaultNoteRecord


def _note(
    *,
    slug: str,
    tags: list[str],
    status: str,
    source_type: str = "article",
    rating: int | None = 7,
    read_time: int | None = 5,
    vaultmind: bool = True,
    flashcards: bool = False,
    saved: str = "2026-03-30T10:00:00+00:00",
) -> VaultNoteRecord:
    body = "# Note\n\n"
    if flashcards:
        body += "## 🃏 Flashcards\n**Q:** Q\n**A:** A\n"
    return VaultNoteRecord(
        path=Path(f"/tmp/{slug}.md"),
        relative_path=f"📚 Sources/AI/{slug}",
        title=slug,
        saved_at=datetime.fromisoformat(saved),
        tags=tags,
        source_type=source_type,
        rating=rating,
        read_time_minutes=read_time,
        status=status,
        canonical_url=None,
        source=None,
        vaultmind=vaultmind,
        body=body,
        summary="s",
        raw_frontmatter={},
    )


def test_compute_vault_stats_counts_and_averages(test_config):
    notes = [
        _note(slug="n1", tags=["ai", "ml"], status="processed", flashcards=True),
        _note(slug="n2", tags=["ai"], status="partial", source_type="reddit", rating=9, read_time=7),
        _note(slug="n3", tags=[], status="review", source_type="github", rating=None, read_time=None),
    ]

    stats = compute_vault_stats(notes, test_config)
    assert stats.total_notes == 3
    assert stats.by_type["article"] == 1
    assert stats.by_type["reddit"] == 1
    assert stats.by_status["partial"] == 1
    assert stats.avg_rating is not None
    assert stats.flashcard_coverage_pct > 0
    assert stats.tagless_note_paths == ["📚 Sources/AI/n3"]
    assert "📚 Sources/AI/n2" in stats.partial_or_review_paths


def test_compute_vault_stats_detects_moc_candidates(test_config):
    notes = [
        _note(slug=f"n{i}", tags=["ai"], status="processed")
        for i in range(5)
    ]
    stats = compute_vault_stats(notes, test_config)
    assert ("ai", 5) in stats.moc_candidates
