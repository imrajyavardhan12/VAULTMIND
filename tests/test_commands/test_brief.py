"""Tests for vm brief command."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from vaultmind.ai.knowledge import WeeklyBrief
from vaultmind.core.vault_index import VaultNoteRecord


def _note(slug: str, saved: str) -> VaultNoteRecord:
    return VaultNoteRecord(
        path=Path(f"/tmp/{slug}.md"),
        relative_path=f"📚 Sources/AI/{slug}",
        title=slug,
        saved_at=datetime.fromisoformat(saved),
        tags=["ai"],
        source_type="article",
        rating=7,
        read_time_minutes=5,
        status="processed",
        canonical_url=None,
        source=None,
        vaultmind=True,
        body="# body",
        summary="summary",
        raw_frontmatter={},
    )


def test_brief_filters_by_days_and_uses_fast_tier(monkeypatch, test_config):
    from vaultmind.commands import brief as brief_cmd

    called: dict[str, object] = {}

    notes = [
        _note("recent", "2026-04-10T10:00:00+00:00"),
        _note("old", "2026-01-01T10:00:00+00:00"),
    ]

    monkeypatch.setattr(brief_cmd, "setup_logging", lambda verbose=False: None)
    monkeypatch.setattr(brief_cmd, "load_config", lambda: test_config)
    monkeypatch.setattr(brief_cmd, "scan_vault_notes", lambda config, only_vaultmind=True: notes)
    real_filter = brief_cmd.filter_notes_by_days
    monkeypatch.setattr(
        brief_cmd,
        "filter_notes_by_days",
        lambda notes, *, days, now=None: real_filter(
            notes, days=days, now=datetime(2026, 4, 11, tzinfo=UTC)
        ),
    )

    def fake_get_provider(config, tier="fast"):
        called["tier"] = tier
        return object()

    async def fake_generate(notes, provider, *, period_label):
        called["note_count"] = len(notes)
        return WeeklyBrief(
            period_label=period_label,
            one_sentence_takeaway="takeaway",
            themes=[],
            highlights=[],
            gaps=[],
            suggested_next_steps=[],
        )

    monkeypatch.setattr(brief_cmd, "get_provider", fake_get_provider)
    monkeypatch.setattr(brief_cmd, "generate_weekly_brief", fake_generate)
    monkeypatch.setattr(brief_cmd, "render_weekly_brief", lambda report: None)

    brief_cmd.brief(days=7, limit=20, verbose=False)
    assert called["tier"] == "fast"
    assert called["note_count"] == 1


def test_brief_skips_ai_when_empty(monkeypatch, test_config):
    from vaultmind.commands import brief as brief_cmd

    called = {"warned": False, "provider": False}
    monkeypatch.setattr(brief_cmd, "setup_logging", lambda verbose=False: None)
    monkeypatch.setattr(brief_cmd, "load_config", lambda: test_config)
    monkeypatch.setattr(brief_cmd, "scan_vault_notes", lambda config, only_vaultmind=True: [])
    monkeypatch.setattr(brief_cmd, "print_warning", lambda message: called.__setitem__("warned", True))
    monkeypatch.setattr(brief_cmd, "get_provider", lambda config, tier="fast": called.__setitem__("provider", True))

    brief_cmd.brief(days=7, limit=20, verbose=False)
    assert called["warned"] is True
    assert called["provider"] is False
