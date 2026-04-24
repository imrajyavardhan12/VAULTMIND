"""Tests for vm flashcard command helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from vaultmind.commands.flashcard import FlashcardSession, QuizCard, build_quiz_cards
from vaultmind.core.flashcards import NoteFlashcardDeck
from vaultmind.core.vault_index import VaultNoteRecord
from vaultmind.schemas import Flashcard


def _deck(slug: str, tags: list[str], cards: int) -> NoteFlashcardDeck:
    note = VaultNoteRecord(
        path=Path(f"/tmp/{slug}.md"),
        relative_path=f"📚 Sources/AI/{slug}",
        title=slug,
        saved_at=datetime.now(UTC),
        tags=tags,
        source_type="article",
        rating=8,
        read_time_minutes=5,
        status="processed",
        canonical_url=None,
        source=None,
        vaultmind=True,
        body="# body",
        summary="summary",
        raw_frontmatter={},
    )
    return NoteFlashcardDeck(
        note=note,
        cards=[Flashcard(question=f"Q{i}", answer=f"A{i}") for i in range(cards)],
    )


def test_build_quiz_cards_filters_by_topic():
    decks = [_deck("ai-note", ["ai"], 2), _deck("bio-note", ["biology"], 2)]
    cards = build_quiz_cards(decks, topic="ai", limit=10)
    assert cards
    assert all("ai-note" in card.note_path for card in cards)


def test_build_quiz_cards_respects_limit():
    decks = [_deck("a", ["ai"], 5), _deck("b", ["ai"], 5)]
    cards = build_quiz_cards(decks, limit=3)
    assert len(cards) == 3


def test_flashcard_session_state_transitions():
    cards = [
        QuizCard(note_title="n1", note_path="p1", card=Flashcard(question="Q1", answer="A1")),
        QuizCard(note_title="n2", note_path="p2", card=Flashcard(question="Q2", answer="A2")),
    ]
    session = FlashcardSession(cards=cards)

    assert session.current().card.question == "Q1"
    session.flip()
    assert session.flipped is True
    session.next()
    assert session.current().card.question == "Q2"
    assert session.flipped is False
    session.mark_known()
    assert session.known == [1]
    session.previous()
    session.mark_unsure()
    assert session.unsure == [0]
