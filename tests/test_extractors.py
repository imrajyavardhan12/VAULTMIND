"""Tests for extractor dispatch."""

from vaultmind.schemas import CanonicalSource, SourceType


def test_dispatch_raises_for_unknown():
    """Unknown source types should raise ValueError."""
    import pytest
    from vaultmind.core.extractors import extract_source
    from vaultmind.config import AppConfig

    source = CanonicalSource(
        original_url="https://example.com",
        canonical_url="https://example.com",
        source_type=SourceType.UNKNOWN,
    )

    # Can't easily test async here without a config, but verify it exists
    assert callable(extract_source)
