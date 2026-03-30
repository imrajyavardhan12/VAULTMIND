"""Extractor dispatch — routes to the right extractor by source type."""

from __future__ import annotations

from vaultmind.config import AppConfig
from vaultmind.schemas import CanonicalSource, ExtractedContent, SourceType


async def extract_source(source: CanonicalSource, config: AppConfig) -> ExtractedContent:
    """Dispatch to the appropriate extractor based on source type."""
    if source.source_type == SourceType.ARTICLE:
        from vaultmind.core.scraper import extract_article

        return await extract_article(source)

    if source.source_type == SourceType.REDDIT:
        from vaultmind.core.reddit import extract_reddit

        return await extract_reddit(source, config)

    if source.source_type == SourceType.GITHUB:
        from vaultmind.core.github import extract_github

        return await extract_github(source, config)

    if source.source_type == SourceType.TWEET:
        from vaultmind.core.twitter import extract_tweet

        return await extract_tweet(source)

    raise ValueError(f"Unsupported source type: {source.source_type}")
