"""Article extraction using trafilatura."""

from __future__ import annotations

import structlog
import trafilatura

from vaultmind.schemas import CanonicalSource, ExtractedContent

log = structlog.get_logger()


async def extract_article(source: CanonicalSource) -> ExtractedContent:
    """Extract clean text content from an article URL using trafilatura."""
    log.info("extracting_article", url=source.canonical_url)

    downloaded = trafilatura.fetch_url(source.canonical_url)
    if downloaded is None:
        log.warning("fetch_failed", url=source.canonical_url)
        return ExtractedContent(
            source=source,
            title=source.canonical_url,
            text="",
            word_count=0,
        )

    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    ) or ""

    metadata = trafilatura.extract(
        downloaded,
        output_format="json",
        include_comments=False,
    )

    title = ""
    author = None
    site_name = None
    date_published = None

    if metadata:
        import json

        try:
            meta_dict = json.loads(metadata)
            title = meta_dict.get("title", "")
            author = meta_dict.get("author") or None
            site_name = meta_dict.get("sitename") or None
            date_published = meta_dict.get("date") or None
        except (json.JSONDecodeError, TypeError):
            pass

    if not title:
        title = source.canonical_url.split("/")[-1].replace("-", " ").title()

    word_count = len(text.split()) if text else 0

    log.info("extraction_complete", title=title, word_count=word_count)

    return ExtractedContent(
        source=source,
        title=title,
        text=text,
        author=author,
        site_name=site_name,
        date_published=date_published,
        word_count=word_count,
    )
