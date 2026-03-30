"""Tests for related-note linking."""

from __future__ import annotations

from pathlib import Path

import yaml

from vaultmind.core.linker import find_related_notes


def _write_note(tmp_vault: Path, rel_path: str, frontmatter: dict) -> Path:
    path = tmp_vault / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{fm}---\n\n# Body\n", encoding="utf-8")
    return path


def test_find_related_notes_empty_vault_returns_empty_list(test_config):
    result = find_related_notes(
        current_title="AI Agents",
        current_tags=["ai", "automation"],
        current_canonical_url="https://example.com/current",
        config=test_config,
    )
    assert result == []


def test_find_related_notes_skips_non_vaultmind_notes(test_config):
    _write_note(
        test_config.vault_path,
        "📚 Sources/AI/non-vaultmind.md",
        {
            "title": "Non VaultMind Note",
            "canonical_url": "https://example.com/other",
            "tags": ["ai"],
            "vaultmind": False,
        },
    )

    result = find_related_notes(
        current_title="AI Agents",
        current_tags=["ai"],
        current_canonical_url="https://example.com/current",
        config=test_config,
    )
    assert result == []


def test_find_related_notes_skips_current_note_by_canonical_url(test_config):
    _write_note(
        test_config.vault_path,
        "📚 Sources/AI/current.md",
        {
            "title": "Current Note",
            "canonical_url": "https://example.com/current",
            "tags": ["ai", "agents"],
            "vaultmind": True,
        },
    )

    result = find_related_notes(
        current_title="Current Note",
        current_tags=["ai", "agents"],
        current_canonical_url="https://example.com/current",
        config=test_config,
    )
    assert result == []


def test_find_related_notes_scores_higher_for_more_shared_tags(test_config):
    _write_note(
        test_config.vault_path,
        "📚 Sources/AI/high-match.md",
        {
            "title": "High Match",
            "canonical_url": "https://example.com/high",
            "tags": ["ai", "python", "automation"],
            "vaultmind": True,
        },
    )
    _write_note(
        test_config.vault_path,
        "📚 Sources/AI/low-match.md",
        {
            "title": "Low Match",
            "canonical_url": "https://example.com/low",
            "tags": ["ai"],
            "vaultmind": True,
        },
    )

    result = find_related_notes(
        current_title="AI Python Automation",
        current_tags=["ai", "python", "automation"],
        current_canonical_url="https://example.com/current",
        config=test_config,
    )

    assert len(result) >= 2
    assert result[0].title == "High Match"
    assert result[0].score > result[1].score


def test_find_related_notes_uses_title_tokens_as_secondary_signal(test_config):
    _write_note(
        test_config.vault_path,
        "📚 Sources/Tech/title-overlap.md",
        {
            "title": "Deep Systems for Focus",
            "canonical_url": "https://example.com/title-overlap",
            "tags": ["history"],
            "vaultmind": True,
        },
    )

    result = find_related_notes(
        current_title="Deep Work Systems",
        current_tags=["biology"],
        current_canonical_url="https://example.com/current",
        config=test_config,
    )

    assert len(result) == 1
    assert result[0].title == "Deep Systems for Focus"


def test_find_related_notes_caps_results_at_limit(test_config):
    for i in range(6):
        _write_note(
            test_config.vault_path,
            f"📚 Sources/AI/note-{i}.md",
            {
                "title": f"Note {i}",
                "canonical_url": f"https://example.com/{i}",
                "tags": ["ai"],
                "vaultmind": True,
            },
        )

    result = find_related_notes(
        current_title="AI Notes",
        current_tags=["ai"],
        current_canonical_url="https://example.com/current",
        config=test_config,
        limit=3,
    )
    assert len(result) == 3


def test_find_related_notes_returns_vault_relative_posix_path(test_config):
    _write_note(
        test_config.vault_path,
        "📚 Sources/AI/the-attention-economy-is-broken.md",
        {
            "title": "The Attention Economy Is Broken",
            "canonical_url": "https://example.com/attention",
            "tags": ["ai", "attention"],
            "vaultmind": True,
        },
    )

    result = find_related_notes(
        current_title="Attention Systems",
        current_tags=["attention"],
        current_canonical_url="https://example.com/current",
        config=test_config,
    )

    assert len(result) == 1
    assert result[0].path == "📚 Sources/AI/the-attention-economy-is-broken"


def test_find_related_notes_sorts_by_score_then_shared_tags_then_title(test_config):
    _write_note(
        test_config.vault_path,
        "📚 Sources/AI/beta.md",
        {
            "title": "Beta Note",
            "canonical_url": "https://example.com/beta",
            "tags": ["ai", "tools"],
            "vaultmind": True,
        },
    )
    _write_note(
        test_config.vault_path,
        "📚 Sources/AI/alpha.md",
        {
            "title": "Alpha Note",
            "canonical_url": "https://example.com/alpha",
            "tags": ["ai", "tools"],
            "vaultmind": True,
        },
    )

    result = find_related_notes(
        current_title="Completely Different",
        current_tags=["ai", "tools"],
        current_canonical_url="https://example.com/current",
        config=test_config,
    )

    assert [item.title for item in result] == ["Alpha Note", "Beta Note"]
