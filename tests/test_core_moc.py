"""Tests for MOC helper utilities."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from vaultmind.ai.knowledge import MocSection, TopicDigest
from vaultmind.core.moc import get_moc_path, render_moc_markdown, should_generate_moc
from vaultmind.core.search import SearchMatch
from vaultmind.core.vault_index import VaultNoteRecord


def _make_note(slug: str) -> VaultNoteRecord:
    return VaultNoteRecord(
        path=Path(f"/tmp/{slug}.md"),
        relative_path=f"📚 Sources/AI/{slug}",
        title=slug,
        saved_at=datetime.now(UTC),
        tags=["ai"],
        source_type="article",
        rating=8,
        read_time_minutes=4,
        status="processed",
        canonical_url=None,
        source=None,
        vaultmind=True,
        body="# body",
        summary="summary",
        raw_frontmatter={},
    )


def test_get_moc_path_uses_slug(test_config):
    path = get_moc_path("Machine Learning", test_config)
    assert path.name == "machine-learning-moc.md"


def test_should_generate_moc_threshold_gating():
    assert should_generate_moc("ai", [1, 2, 3, 4], min_notes=5) is False
    assert should_generate_moc("ai", [1, 2, 3, 4, 5], min_notes=5) is True


def test_render_moc_markdown_contains_wikilinks():
    digest = TopicDigest(
        topic="ai",
        thesis="A thesis",
        patterns=["Pattern 1"],
        tensions=["Tension 1"],
        standout_notes=[],
        open_questions=["Question 1"],
        moc_sections=[MocSection(heading="Core", summary="S", note_paths=["📚 Sources/AI/a"])],
    )
    matches = [
        SearchMatch(note=_make_note("a"), score=50, title_hits=[], tag_hits=[], excerpt=""),
        SearchMatch(note=_make_note("b"), score=40, title_hits=[], tag_hits=[], excerpt=""),
    ]

    markdown = render_moc_markdown("AI", digest, matches)
    assert "[[📚 Sources/AI/a|a]]" in markdown
    assert "[[📚 Sources/AI/b|b]]" in markdown
