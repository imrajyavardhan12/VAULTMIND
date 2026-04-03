"""Tests for AI knowledge synthesis layer."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from vaultmind.ai.knowledge import (
    generate_reflection,
    generate_topic_digest,
    generate_weekly_brief,
)
from vaultmind.core.search import SearchMatch
from vaultmind.core.vault_index import VaultNoteRecord


class StubProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.model = "stub-model"

    async def complete(self, prompt: str, system: str = "") -> str:
        del prompt, system
        return self.response


def _note(title: str, path_slug: str) -> VaultNoteRecord:
    return VaultNoteRecord(
        path=Path(f"/tmp/{path_slug}.md"),
        relative_path=f"📚 Sources/AI/{path_slug}",
        title=title,
        saved_at=datetime.now(timezone.utc),
        tags=["ai", "tools"],
        source_type="article",
        rating=8,
        read_time_minutes=6,
        status="processed",
        canonical_url=None,
        source=None,
        vaultmind=True,
        body="# Body",
        summary="Summary text",
        raw_frontmatter={},
    )


def test_generate_weekly_brief_parses_valid_json():
    provider = StubProvider(
        '{"period_label":"Last 7 days","one_sentence_takeaway":"Takeaway","themes":[{"name":"AI","insight":"x"}],'
        '"highlights":[{"title":"N1","path":"📚 Sources/AI/n1","reason":"r"}],"gaps":["g"],'
        '"suggested_next_steps":["s"]}'
    )
    result = asyncio.run(generate_weekly_brief([_note("N1", "n1")], provider, period_label="Last 7 days"))
    assert result.one_sentence_takeaway == "Takeaway"
    assert result.themes[0].name == "AI"


def test_generate_weekly_brief_fallback_on_invalid_json():
    provider = StubProvider("not-json")
    result = asyncio.run(generate_weekly_brief([_note("N1", "n1")], provider, period_label="Last 7 days"))
    assert result.period_label == "Last 7 days"
    assert result.one_sentence_takeaway


def test_generate_topic_digest_parses_valid_json():
    provider = StubProvider(
        '{"topic":"ai","thesis":"T","patterns":["p"],"tensions":["t"],'
        '"standout_notes":[{"title":"N1","path":"📚 Sources/AI/n1","reason":"r"}],'
        '"open_questions":["q"],"moc_sections":[{"heading":"Core","summary":"s","note_paths":["📚 Sources/AI/n1"]}]}'
    )
    matches = [SearchMatch(note=_note("N1", "n1"), score=80, title_hits=[], tag_hits=[], excerpt="")]
    result = asyncio.run(generate_topic_digest("ai", matches, provider))
    assert result.topic == "ai"
    assert result.thesis == "T"


def test_generate_reflection_parses_valid_json():
    provider = StubProvider(
        '{"period_label":"Last 7 days","dominant_themes":["AI"],"belief_shifts":["shift"],'
        '"tensions":["t"],"blindspots":["b"],"questions_for_you":["q"],'
        '"recommended_experiment":"exp"}'
    )
    result = asyncio.run(generate_reflection([_note("N1", "n1")], provider, period_label="Last 7 days"))
    assert result.recommended_experiment == "exp"


def test_generate_reflection_fallback_on_invalid_json():
    provider = StubProvider("{")
    result = asyncio.run(generate_reflection([_note("N1", "n1")], provider, period_label="Last 7 days"))
    assert result.period_label == "Last 7 days"
    assert result.recommended_experiment
