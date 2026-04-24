"""Tests for raw source scanning."""

from __future__ import annotations

from vaultmind.core.raw_scanner import scan_raw_sources


def test_scan_raw_sources_prefers_canonical_raw_folder(test_config):
    raw_note = test_config.vault_path / "📥 Raw" / "article.md"
    raw_note.parent.mkdir(parents=True, exist_ok=True)
    raw_note.write_text(
        "---\nsource: https://example.com/a\ntags: [ai]\n---\n\n# Article\n\nBody",
        encoding="utf-8",
    )

    records = scan_raw_sources(test_config)

    assert len(records) == 1
    assert records[0].relative_path == "📥 Raw/article"
    assert records[0].source_url == "https://example.com/a"


def test_scan_raw_sources_falls_back_to_legacy_clippings(test_config):
    legacy_note = test_config.vault_path / "Clippings" / "legacy.md"
    legacy_note.parent.mkdir(parents=True, exist_ok=True)
    legacy_note.write_text("# Legacy\n\nOriginal body", encoding="utf-8")

    records = scan_raw_sources(test_config)

    assert len(records) == 1
    assert records[0].relative_path == "Clippings/legacy"
    assert records[0].title == "Legacy"
