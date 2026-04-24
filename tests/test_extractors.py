"""Tests for extractor dispatch."""

import pytest

from vaultmind.core.extractors import extract_source
from vaultmind.schemas import CanonicalSource, SourceType


async def test_dispatch_raises_for_unknown(test_config):
    """Unknown source types should raise ValueError."""
    source = CanonicalSource(
        original_url="https://example.com",
        canonical_url="https://example.com",
        source_type=SourceType.UNKNOWN,
    )

    with pytest.raises(ValueError, match="Unsupported source type"):
        await extract_source(source, test_config)
