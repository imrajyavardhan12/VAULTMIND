"""vm flashcard — quiz mode over saved flashcards."""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field

import typer
from rich.panel import Panel

from vaultmind.config import load_config
from vaultmind.core.flashcards import NoteFlashcardDeck, collect_flashcard_decks
from vaultmind.core.search import search_notes
from vaultmind.core.vault_index import scan_vault_notes
from vaultmind.schemas import Flashcard
from vaultmind.utils.display import console, print_warning
from vaultmind.utils.logging import setup_logging


@dataclass(slots=True)
class QuizCard:
    note_title: str
    note_path: str
    card: Flashcard


@dataclass(slots=True)
class FlashcardSession:
    cards: list[QuizCard]
    index: int = 0
    flipped: bool = False
    known: list[int] = field(default_factory=list)
    unsure: list[int] = field(default_factory=list)

    def current(self) -> QuizCard:
        return self.cards[self.index]

    def flip(self) -> None:
        self.flipped = not self.flipped

    def next(self) -> None:
        self.index = (self.index + 1) % len(self.cards)
        self.flipped = False

    def previous(self) -> None:
        self.index = (self.index - 1) % len(self.cards)
        self.flipped = False

    def mark_known(self) -> None:
        if self.index not in self.known:
            self.known.append(self.index)
        if self.index in self.unsure:
            self.unsure.remove(self.index)

    def mark_unsure(self) -> None:
        if self.index not in self.unsure:
            self.unsure.append(self.index)
        if self.index in self.known:
            self.known.remove(self.index)


def flashcard(topic: str | None = None, limit: int = 30, verbose: bool = False) -> None:
    """Run flashcard quiz mode using stored cards (no AI call)."""
    setup_logging(verbose=verbose)
    config = load_config()
    notes = scan_vault_notes(config, only_vaultmind=True)

    if topic:
        matches = search_notes(notes, topic, limit=max(limit * 3, 50))
        notes = [match.note for match in matches]

    decks = collect_flashcard_decks(notes)
    cards = build_quiz_cards(decks, topic=topic, limit=limit)

    if not cards:
        print_warning("No flashcards found for the selected notes/topic.")
        return

    if not sys.stdin.isatty():
        _render_non_interactive(cards)
        return

    _run_interactive_session(cards)


def build_quiz_cards(
    decks: list[NoteFlashcardDeck],
    *,
    topic: str | None = None,
    limit: int = 30,
) -> list[QuizCard]:
    """Flatten and shuffle note decks into quiz cards."""
    topic_query = (topic or "").strip().lower()
    cards: list[QuizCard] = []

    for deck in decks:
        if topic_query:
            haystack = " ".join([deck.note.title, " ".join(deck.note.tags)]).lower()
            if topic_query not in haystack:
                continue

        for card in deck.cards:
            cards.append(
                QuizCard(
                    note_title=deck.note.title,
                    note_path=deck.note.relative_path,
                    card=card,
                )
            )

    random.shuffle(cards)
    return cards[:limit]


def _render_non_interactive(cards: list[QuizCard]) -> None:
    """Render cards without TTY interaction (for pipes/tests/non-interactive shells)."""
    for i, quiz_card in enumerate(cards, 1):
        console.print(
            Panel(
                f"**Q:** {quiz_card.card.question}\n\n**A:** {quiz_card.card.answer}\n\n"
                f"*Source:* {quiz_card.note_path}",
                title=f"Card {i}/{len(cards)}",
                border_style="green",
            )
        )


def _run_interactive_session(cards: list[QuizCard]) -> None:
    """Simple keyboard-driven flashcard session."""
    session = FlashcardSession(cards=cards)
    while True:
        current = session.current()
        progress = f"{session.index + 1}/{len(cards)}"
        status = f"Known: {len(session.known)} | Unsure: {len(session.unsure)}"

        if session.flipped:
            content = (
                f"**Q:** {current.card.question}\n\n"
                f"**A:** {current.card.answer}\n\n"
                f"*Source:* {current.note_path}\n\n"
                f"{status}"
            )
        else:
            content = f"**Q:** {current.card.question}\n\n*Press space to flip*\n\n{status}"

        console.print(Panel(content, title=f"Flashcard {progress}", border_style="cyan"))
        prompt = "[space]=flip, [n]=next, [p]=prev, [k]=known, [u]=unsure, [q]=quit: "
        command = input(prompt).strip().lower()

        if command in {"", " "}:
            session.flip()
        elif command == "n":
            session.next()
        elif command == "p":
            session.previous()
        elif command == "k":
            session.mark_known()
            session.next()
        elif command == "u":
            session.mark_unsure()
            session.next()
        elif command == "q":
            break


if __name__ == "__main__":
    typer.run(flashcard)
