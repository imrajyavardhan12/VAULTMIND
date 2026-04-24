"""Tests for keyword/fuzzy search scoring."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from vaultmind.core.search import build_match_excerpt, search_notes
from vaultmind.core.vault_index import VaultNoteRecord


def _note(
    *,
    title: str,
    tags: list[str],
    body: str,
    saved_at: str = "2026-03-30T10:00:00+00:00",
    path_slug: str = "note",
) -> VaultNoteRecord:
    return VaultNoteRecord(
        path=Path(f"/tmp/{path_slug}.md"),
        relative_path=f"📚 Sources/AI/{path_slug}",
        title=title,
        saved_at=datetime.fromisoformat(saved_at),
        tags=tags,
        source_type="article",
        rating=7,
        read_time_minutes=5,
        status="processed",
        canonical_url=f"https://example.com/{path_slug}",
        source=f"https://example.com/{path_slug}",
        vaultmind=True,
        body=body,
        summary=body[:80],
        raw_frontmatter={},
    )


def test_exact_title_match_beats_body_match():
    title_note = _note(title="Machine Learning Notes", tags=["ai"], body="generic body", path_slug="title")
    body_note = _note(title="General Notes", tags=["misc"], body="... machine learning ...", path_slug="body")
    matches = search_notes([body_note, title_note], "machine learning")
    assert matches[0].note.title == "Machine Learning Notes"


def test_tag_match_scores_above_body_only_match():
    tag_note = _note(title="General", tags=["machine-learning"], body="generic", path_slug="tag")
    body_note = _note(title="General", tags=["misc"], body="machine learning in body", path_slug="body")
    matches = search_notes([body_note, tag_note], "machine learning")
    assert matches[0].note.relative_path.endswith("tag")


def test_fuzzy_match_handles_typos():
    note = _note(title="Attention Economy", tags=["psychology"], body="text", path_slug="attn")
    matches = search_notes([note], "attenton economi")
    assert len(matches) == 1


def test_build_match_excerpt_centers_around_query():
    body = "A " * 200 + "critical query phrase" + " B" * 200
    excerpt = build_match_excerpt(body, "query phrase", radius=40)
    assert "query phrase" in excerpt.lower()
    assert len(excerpt) < len(body)


def test_empty_query_returns_recent_notes():
    newer = _note(
        title="New",
        tags=["ai"],
        body="x",
        saved_at="2026-03-30T10:00:00+00:00",
        path_slug="new",
    )
    older = _note(
        title="Old",
        tags=["ai"],
        body="x",
        saved_at="2026-03-01T10:00:00+00:00",
        path_slug="old",
    )

    matches = search_notes([older, newer], "", limit=20)
    assert len(matches) == 2
    assert matches[0].note.title == "New"
