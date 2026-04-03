"""Tests for core flashcard extraction."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vaultmind.core.flashcards import collect_flashcard_decks, extract_flashcards_from_body
from vaultmind.core.vault_index import VaultNoteRecord


def _note_with_body(body: str, slug: str = "note") -> VaultNoteRecord:
    return VaultNoteRecord(
        path=Path(f"/tmp/{slug}.md"),
        relative_path=f"📚 Sources/AI/{slug}",
        title=slug,
        saved_at=datetime.now(timezone.utc),
        tags=["ai"],
        source_type="article",
        rating=7,
        read_time_minutes=5,
        status="processed",
        canonical_url=None,
        source=None,
        vaultmind=True,
        body=body,
        summary="summary",
        raw_frontmatter={},
    )


def test_extract_flashcards_from_body_parses_qa_pairs():
    body = """# Note

## 🃏 Flashcards
**Q:** What is VaultMind?
**A:** A CLI for processing links.

**Q:** Why use it?
**A:** To build a better knowledge vault.
"""
    cards = extract_flashcards_from_body(body)
    assert len(cards) == 2
    assert cards[0].question == "What is VaultMind?"


def test_collect_flashcard_decks_skips_notes_without_section():
    notes = [_note_with_body("# Note\n\nNo flashcards", "no-cards")]
    decks = collect_flashcard_decks(notes)
    assert decks == []


def test_extract_flashcards_handles_malformed_pairs():
    body = """## 🃏 Flashcards
**Q:** Question only
random text
**A:** Proper answer
"""
    cards = extract_flashcards_from_body(body)
    assert len(cards) == 1
    assert cards[0].answer == "Proper answer"
