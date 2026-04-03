"""Tests for tag normalization helpers."""

from vaultmind.utils.tags import normalize_tag, normalize_tags


def test_normalize_tag_kebab_case_and_lowercase():
    assert normalize_tag("Large Language Models") == "large-language-models"
    assert normalize_tag("multi-head attention") == "multi-head-attention"


def test_normalize_tag_strips_hash_and_punctuation():
    assert normalize_tag("#Attention mechanisms!") == "attention-mechanisms"


def test_normalize_tag_preserves_nested_segments():
    assert normalize_tag("LLM / Attention mechanisms") == "llm/attention-mechanisms"


def test_normalize_tags_dedupes_and_omits_empty():
    tags = normalize_tags(["AI", "ai", "#AI", "  ", "attention mechanisms"])
    assert tags == ["ai", "attention-mechanisms"]
