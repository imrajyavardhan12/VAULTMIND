"""Flashcard extraction utilities for Phase 4 quiz mode."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from vaultmind.core.vault_index import VaultNoteRecord
from vaultmind.schemas import Flashcard


@dataclass(slots=True)
class NoteFlashcardDeck:
    note: VaultNoteRecord
    cards: list[Flashcard]


def extract_flashcards_from_body(body: str) -> list[Flashcard]:
    """Extract flashcards from a `## 🃏 Flashcards` markdown section."""
    lines = body.splitlines()
    in_section = False
    question: str | None = None
    cards: list[Flashcard] = []

    for line in lines:
        stripped = line.strip()

        if not in_section:
            if re.match(r"^##\s*🃏\s*Flashcards\s*$", stripped, flags=re.IGNORECASE):
                in_section = True
            continue

        if stripped.startswith("## "):
            break

        if stripped.startswith("**Q:**"):
            question = stripped[len("**Q:**") :].strip() or None
            continue

        if stripped.startswith("**A:**") and question:
            answer = stripped[len("**A:**") :].strip()
            if answer:
                cards.append(Flashcard(question=question, answer=answer))
            question = None

    return cards


def collect_flashcard_decks(notes: Sequence[VaultNoteRecord]) -> list[NoteFlashcardDeck]:
    """Collect flashcard decks from notes that contain flashcard sections."""
    decks: list[NoteFlashcardDeck] = []
    for note in notes:
        cards = extract_flashcards_from_body(note.body)
        if cards:
            decks.append(NoteFlashcardDeck(note=note, cards=cards))
    return decks
