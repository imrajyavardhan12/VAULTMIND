"""Tests for vault indexing and note parsing."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from vaultmind.core.vault_index import (
    extract_summary_from_body,
    filter_notes_by_days,
    parse_saved_at,
    scan_vault_notes,
)


def _write_note(path: Path, frontmatter: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{fm}---\n\n{body}\n", encoding="utf-8")


def test_scan_vault_notes_returns_records(test_config):
    note_path = test_config.vault_path / "📚 Sources" / "AI" / "note-a.md"
    _write_note(
        note_path,
        {
            "title": "Note A",
            "saved": "2026-03-29T10:00:00Z",
            "tags": ["ai", "tools"],
            "type": "article",
            "vaultmind": True,
        },
        "# Note A\n\n## 🧠 Summary\nA concise summary.",
    )

    records = scan_vault_notes(test_config)
    assert len(records) == 1
    assert records[0].title == "Note A"
    assert records[0].relative_path.endswith("📚 Sources/AI/note-a")
    assert records[0].summary == "A concise summary."


def test_scan_vault_notes_skips_non_vaultmind_by_default(test_config):
    path = test_config.vault_path / "📚 Sources" / "Tech" / "external.md"
    _write_note(
        path,
        {"title": "External", "saved": "2026-03-28T10:00:00Z", "vaultmind": False},
        "# External\n\nContent",
    )

    assert scan_vault_notes(test_config) == []
    assert len(scan_vault_notes(test_config, only_vaultmind=False)) == 1


def test_filter_notes_by_days(test_config):
    now = datetime(2026, 3, 30, tzinfo=timezone.utc)
    recent_path = test_config.vault_path / "📚 Sources" / "AI" / "recent.md"
    old_path = test_config.vault_path / "📚 Sources" / "AI" / "old.md"

    _write_note(
        recent_path,
        {"title": "Recent", "saved": "2026-03-29T10:00:00Z", "vaultmind": True},
        "# Recent\n\nBody",
    )
    _write_note(
        old_path,
        {"title": "Old", "saved": "2026-01-01T10:00:00Z", "vaultmind": True},
        "# Old\n\nBody",
    )

    records = scan_vault_notes(test_config)
    filtered = filter_notes_by_days(records, days=7, now=now)
    assert len(filtered) == 1
    assert filtered[0].title == "Recent"


def test_parse_saved_at_handles_iso_z_and_invalid():
    parsed = parse_saved_at("2026-03-30T10:15:00Z")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parse_saved_at("not-a-date") is None


def test_extract_summary_from_multiple_heading_variants():
    body = "# Title\n\n## 🧠 Discussion Summary\nDiscussion summary text.\n\n## Other\nx"
    assert extract_summary_from_body(body) == "Discussion summary text."
