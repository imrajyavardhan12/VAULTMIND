"""Tests for vm reflect command."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from vaultmind.ai.knowledge import ReflectionReport
from vaultmind.core.vault_index import VaultNoteRecord


def _note(slug: str, saved: str) -> VaultNoteRecord:
    return VaultNoteRecord(
        path=Path(f"/tmp/{slug}.md"),
        relative_path=f"📚 Sources/AI/{slug}",
        title=slug,
        saved_at=datetime.fromisoformat(saved),
        tags=["ai"],
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


def test_reflect_uses_deep_tier_and_filters_days(monkeypatch, test_config):
    from vaultmind.commands import reflect as reflect_cmd

    called: dict[str, object] = {}
    notes = [
        _note("recent", "2026-04-10T10:00:00+00:00"),
        _note("old", "2026-01-01T10:00:00+00:00"),
    ]

    monkeypatch.setattr(reflect_cmd, "setup_logging", lambda verbose=False: None)
    monkeypatch.setattr(reflect_cmd, "load_config", lambda: test_config)
    monkeypatch.setattr(reflect_cmd, "scan_vault_notes", lambda config, only_vaultmind=True: notes)
    real_filter = reflect_cmd.filter_notes_by_days
    monkeypatch.setattr(
        reflect_cmd,
        "filter_notes_by_days",
        lambda notes, *, days, now=None: real_filter(
            notes, days=days, now=datetime(2026, 4, 11, tzinfo=UTC)
        ),
    )

    def fake_get_provider(config, tier="fast"):
        called["tier"] = tier
        return object()

    async def fake_generate(selected, provider, *, period_label):
        called["count"] = len(selected)
        return ReflectionReport(
            period_label=period_label,
            dominant_themes=[],
            belief_shifts=[],
            tensions=[],
            blindspots=[],
            questions_for_you=[],
            recommended_experiment="exp",
        )

    monkeypatch.setattr(reflect_cmd, "get_provider", fake_get_provider)
    monkeypatch.setattr(reflect_cmd, "generate_reflection", fake_generate)
    monkeypatch.setattr(reflect_cmd, "render_reflection", lambda report, supporting_notes: None)

    reflect_cmd.reflect(days=7, limit=20, verbose=False)
    assert called["tier"] == "deep"
    assert called["count"] == 1
