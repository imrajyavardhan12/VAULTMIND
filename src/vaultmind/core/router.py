"""URL router — detects source type and creates a CanonicalSource."""

from __future__ import annotations

from vaultmind.schemas import CanonicalSource, SourceType
from vaultmind.utils.urls import canonicalize_url, detect_source_type


def route_url(url: str) -> CanonicalSource:
    """Canonicalize a URL and detect its source type."""
    canonical = canonicalize_url(url)
    source_type = detect_source_type(canonical)

    if source_type == SourceType.VIDEO:
        source_type = SourceType.UNKNOWN

    return CanonicalSource(
        original_url=url,
        canonical_url=canonical,
        source_type=source_type,
    )
