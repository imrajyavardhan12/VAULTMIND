"""AI synthesis layer for Phase 4 knowledge-generation commands."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import TypeVar

import structlog
from pydantic import BaseModel, Field

from vaultmind.ai.json_utils import clean_json_response
from vaultmind.ai.prompts import (
    KNOWLEDGE_SYSTEM_PROMPT,
    build_reflection_prompt,
    build_topic_digest_prompt,
    build_weekly_brief_prompt,
)
from vaultmind.ai.providers.base import Provider
from vaultmind.core.search import SearchMatch
from vaultmind.core.vault_index import VaultNoteRecord, format_note_packet

log = structlog.get_logger()

ModelT = TypeVar("ModelT", bound=BaseModel)


class BriefTheme(BaseModel):
    name: str
    insight: str


class NoteReference(BaseModel):
    title: str
    path: str
    reason: str = ""


class MocSection(BaseModel):
    heading: str
    summary: str = ""
    note_paths: list[str] = Field(default_factory=list)


class WeeklyBrief(BaseModel):
    period_label: str
    one_sentence_takeaway: str
    themes: list[BriefTheme] = Field(default_factory=list)
    highlights: list[NoteReference] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)


class TopicDigest(BaseModel):
    topic: str
    thesis: str
    patterns: list[str] = Field(default_factory=list)
    tensions: list[str] = Field(default_factory=list)
    standout_notes: list[NoteReference] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    moc_sections: list[MocSection] = Field(default_factory=list)


class ReflectionReport(BaseModel):
    period_label: str
    dominant_themes: list[str] = Field(default_factory=list)
    belief_shifts: list[str] = Field(default_factory=list)
    tensions: list[str] = Field(default_factory=list)
    blindspots: list[str] = Field(default_factory=list)
    questions_for_you: list[str] = Field(default_factory=list)
    recommended_experiment: str


async def generate_weekly_brief(
    notes: Sequence[VaultNoteRecord],
    provider: Provider,
    *,
    period_label: str,
) -> WeeklyBrief:
    """Generate a weekly brief from recent notes."""
    payload = _build_notes_payload(notes)
    prompt = build_weekly_brief_prompt(period_label=period_label, notes_payload=payload)

    try:
        response = await provider.complete(prompt, system=KNOWLEDGE_SYSTEM_PROMPT)
        brief = _parse_json_model(response, WeeklyBrief)
        if not brief.period_label:
            return brief.model_copy(update={"period_label": period_label})
        return brief
    except Exception as exc:
        log.warning("weekly_brief_generation_failed", error=str(exc))
        return _fallback_weekly_brief(notes, period_label=period_label)


async def generate_topic_digest(
    topic: str,
    matches: Sequence[SearchMatch],
    provider: Provider,
) -> TopicDigest:
    """Generate a topic digest from search matches."""
    notes = [match.note for match in matches]
    payload = _build_notes_payload(notes)
    prompt = build_topic_digest_prompt(topic=topic, notes_payload=payload)

    try:
        response = await provider.complete(prompt, system=KNOWLEDGE_SYSTEM_PROMPT)
        digest = _parse_json_model(response, TopicDigest)
        if not digest.topic:
            return digest.model_copy(update={"topic": topic})
        return digest
    except Exception as exc:
        log.warning("topic_digest_generation_failed", topic=topic, error=str(exc))
        return _fallback_topic_digest(topic, matches)


async def generate_reflection(
    notes: Sequence[VaultNoteRecord],
    provider: Provider,
    *,
    period_label: str,
) -> ReflectionReport:
    """Generate a reflection report from recent notes."""
    payload = _build_notes_payload(notes)
    prompt = build_reflection_prompt(period_label=period_label, notes_payload=payload)

    try:
        response = await provider.complete(prompt, system=KNOWLEDGE_SYSTEM_PROMPT)
        report = _parse_json_model(response, ReflectionReport)
        if not report.period_label:
            return report.model_copy(update={"period_label": period_label})
        return report
    except Exception as exc:
        log.warning("reflection_generation_failed", error=str(exc))
        return _fallback_reflection(notes, period_label=period_label)


def _build_notes_payload(notes: Sequence[VaultNoteRecord]) -> str:
    if not notes:
        return "No notes available."
    return "\n\n---\n\n".join(format_note_packet(note, max_chars=900) for note in notes)


def _parse_json_model(response: str, model: type[ModelT]) -> ModelT:
    cleaned = clean_json_response(response)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("Model response must be a JSON object")
    return model(**data)


def _fallback_weekly_brief(notes: Sequence[VaultNoteRecord], *, period_label: str) -> WeeklyBrief:
    top_tags = _top_tags(notes, limit=3)
    themes = [
        BriefTheme(name=tag, insight=f"You repeatedly saved notes about {tag}.")
        for tag in top_tags
    ]
    highlights = [
        NoteReference(title=note.title, path=note.relative_path, reason="Frequently relevant this period.")
        for note in list(notes)[:3]
    ]

    return WeeklyBrief(
        period_label=period_label,
        one_sentence_takeaway=(
            "Your recent notes cluster around a few recurring themes worth consolidating."
        ),
        themes=themes,
        highlights=highlights,
        gaps=["No explicit capture of opposing viewpoints in some topics."],
        suggested_next_steps=['Run `vm digest "top theme"` to synthesize your strongest thread.'],
    )


def _fallback_topic_digest(topic: str, matches: Sequence[SearchMatch]) -> TopicDigest:
    standout = [
        NoteReference(title=match.note.title, path=match.note.relative_path, reason="High relevance score.")
        for match in list(matches)[:3]
    ]
    note_paths = [match.note.relative_path for match in list(matches)[:8]]

    return TopicDigest(
        topic=topic,
        thesis=f"Your saved notes on {topic} point to a coherent but still evolving perspective.",
        patterns=["Recurring operational patterns are visible across multiple notes."],
        tensions=["Some notes optimize for speed while others optimize for rigor."],
        standout_notes=standout,
        open_questions=[f"What would change your current view on {topic}?"],
        moc_sections=[
            MocSection(heading="Core Notes", summary="Most relevant source notes", note_paths=note_paths)
        ],
    )


def _fallback_reflection(
    notes: Sequence[VaultNoteRecord],
    *,
    period_label: str,
) -> ReflectionReport:
    themes = _top_tags(notes, limit=4)
    return ReflectionReport(
        period_label=period_label,
        dominant_themes=themes,
        belief_shifts=["You appear to be moving from consumption toward synthesis."],
        tensions=["Balancing breadth of topics with depth on any single thread."],
        blindspots=["Few explicit notes on disconfirming evidence."],
        questions_for_you=["Which single theme deserves a 30-day deeper focus?"],
        recommended_experiment=(
            "Pick one theme and write a one-page synthesis every Sunday for four weeks."
        ),
    )


def _top_tags(notes: Sequence[VaultNoteRecord], *, limit: int) -> list[str]:
    counts: dict[str, int] = {}
    for note in notes:
        for tag in note.tags:
            counts[tag] = counts.get(tag, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [tag for tag, _ in ranked[:limit]]
