"""Tests for save command."""

from __future__ import annotations

import yaml

from vaultmind.commands.save import _merge_tags, _write_partial_tweet_note
from vaultmind.core.writer import parse_frontmatter
from vaultmind.schemas import CanonicalSource, ExtractedContent, ExtractionWarning, SourceType


def test_merge_tags_normalizes_and_dedupes(tmp_path):
    note_path = tmp_path / "note.md"
    note_path.write_text(
        "---\n"
        "title: Test\n"
        "tags:\n"
        "- transformer\n"
        "- large language models\n"
        "---\n\n"
        "# Body\n",
        encoding="utf-8",
    )

    _merge_tags(note_path, ["Large Language Models", "#Attention mechanisms"])

    text = note_path.read_text(encoding="utf-8")
    end = text.find("---", 3)
    frontmatter = yaml.safe_load(text[3:end])
    assert frontmatter["tags"] == [
        "transformer",
        "large-language-models",
        "attention-mechanisms",
    ]


def test_write_partial_tweet_note_writes_partial_frontmatter_and_body(test_config):
    source = CanonicalSource(
        original_url="https://x.com/user/status/123",
        canonical_url="https://x.com/user/status/123",
        source_type=SourceType.TWEET,
    )
    content = ExtractedContent(
        source=source,
        title="123",
        text="",
        site_name="Twitter/X",
        extraction_quality=0.1,
        warnings=[
            ExtractionWarning(code="javascript_required", message="X returned a JavaScript-required page")
        ],
    )

    path = _write_partial_tweet_note(
        source=source,
        content=content,
        config=test_config,
        tags=["Large Language Models", "x"],
        folder=None,
    )

    assert path.exists()
    fm = parse_frontmatter(path)
    assert fm is not None
    assert fm.get("status") == "partial"
    assert fm.get("type") == "tweet"
    assert fm.get("tags") == ["large-language-models", "x"]

    body = path.read_text(encoding="utf-8")
    assert "Tweet content could not be extracted automatically from X" in body
    assert "[javascript_required]" in body
