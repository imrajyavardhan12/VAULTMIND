"""Twitter/X extraction — experimental fallback via trafilatura."""

from __future__ import annotations

import structlog
import trafilatura

from vaultmind.schemas import (
    CanonicalSource,
    ExtractedContent,
    ExtractionWarning,
)

log = structlog.get_logger()


async def extract_tweet(source: CanonicalSource) -> ExtractedContent:
    """Extract content from a Twitter/X URL using trafilatura as a best-effort fallback.

    Twitter/X has no public API, so this extractor scrapes whatever content
    it can and marks the result as experimental with reduced quality.
    """
    log.info("extracting_tweet", url=source.canonical_url)

    warnings = [
        ExtractionWarning(
            code="experimental",
            message="Twitter/X has no public API; extraction is best-effort via page scraping",
        ),
    ]

    downloaded = trafilatura.fetch_url(source.canonical_url)
    if downloaded is None:
        log.warning("tweet_fetch_failed", url=source.canonical_url)
        warnings.append(ExtractionWarning(code="fetch_failed", message="Could not download page"))
        return ExtractedContent(
            source=source,
            title=source.canonical_url,
            text="",
            extraction_quality=0.1,
            warnings=warnings,
        )

    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        favor_recall=True,
    ) or ""

    title = source.canonical_url.split("/")[-1] if "/" in source.canonical_url else "Tweet"
    word_count = len(text.split()) if text else 0

    if not text:
        warnings.append(ExtractionWarning(code="empty_content", message="No text could be extracted"))

    log.info("tweet_extraction_complete", word_count=word_count, quality=0.5)

    return ExtractedContent(
        source=source,
        title=title,
        text=text,
        site_name="Twitter/X",
        word_count=word_count,
        extraction_quality=0.5,
        warnings=warnings,
    )
