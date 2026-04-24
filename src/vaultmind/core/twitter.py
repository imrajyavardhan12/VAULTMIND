"""Twitter/X extraction with API-first fallback and JS-gate detection."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx
import structlog
import trafilatura
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from vaultmind.schemas import (
    CanonicalSource,
    ExtractedContent,
    ExtractionWarning,
)

log = structlog.get_logger()
_SYNDICATION_URL = "https://cdn.syndication.twimg.com/tweet-result"
_USER_AGENT = "VaultMind/1.0"
_TWEET_ID_PATTERN = re.compile(r"/status/(\d+)")


class TwitterSyndicationError(Exception):
    """Raised on retryable Twitter syndication API failures."""


def _extract_tweet_id(url: str) -> str | None:
    """Extract tweet status id from a canonical Twitter/X URL."""
    path = urlparse(url).path
    match = _TWEET_ID_PATTERN.search(path)
    return match.group(1) if match else None


def _is_javascript_gate_text(text: str) -> bool:
    """Detect X's JavaScript/extension warning page text."""
    normalized = text.casefold().replace("'", "'")
    return (
        "javascript is disabled in this browser" in normalized
        or "please enable javascript or switch to a supported browser" in normalized
        or "privacy related extensions may cause issues on x.com" in normalized
    )


@retry(
    retry=retry_if_exception_type(TwitterSyndicationError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _fetch_syndicated_tweet(tweet_id: str) -> dict[str, Any] | None:
    """Fetch tweet data from Twitter's public syndication endpoint."""
    async with httpx.AsyncClient(
        headers={"User-Agent": _USER_AGENT},
        follow_redirects=True,
        timeout=20.0,
    ) as client:
        resp = await client.get(_SYNDICATION_URL, params={"id": tweet_id, "lang": "en"})

    if resp.status_code == 404:
        return None
    if resp.status_code == 429 or resp.status_code >= 500:
        raise TwitterSyndicationError(f"Syndication returned {resp.status_code}")
    resp.raise_for_status()

    data = resp.json()
    return data if isinstance(data, dict) else None


def _as_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _build_text_from_syndication(data: dict[str, Any]) -> tuple[str, str | None]:
    """Convert syndication JSON into extracted text and author handle."""
    body = _as_text(data.get("text"))

    user = data.get("user")
    author: str | None = None
    if isinstance(user, dict):
        screen_name = _as_text(user.get("screen_name"))
        if screen_name:
            author = f"@{screen_name}"

    parts: list[str] = []
    if body:
        parts.append(body)

    quoted = data.get("quoted_tweet")
    if isinstance(quoted, dict):
        quoted_text = _as_text(quoted.get("text"))
        if quoted_text:
            parts.append(f"Quoted tweet:\n{quoted_text}")

    return "\n\n".join(parts).strip(), author


async def extract_tweet(source: CanonicalSource) -> ExtractedContent:
    """Extract content from a Twitter/X URL using trafilatura as a best-effort fallback.

    Twitter/X has no public API, so this extractor scrapes whatever content
    it can and marks the result as experimental with reduced quality.
    """
    log.info("extracting_tweet", url=source.canonical_url)

    warnings = [
        ExtractionWarning(
            code="experimental",
            message=(
                "Twitter/X extraction is best-effort and may fail for protected or blocked pages"
            ),
        ),
    ]

    tweet_id = _extract_tweet_id(source.canonical_url)
    if tweet_id:
        try:
            syndicated = await _fetch_syndicated_tweet(tweet_id)
        except Exception as exc:
            log.warning("tweet_syndication_failed", url=source.canonical_url, error=str(exc))
            warnings.append(
                ExtractionWarning(code="syndication_failed", message="Syndication API unavailable")
            )
        else:
            if syndicated:
                text, author = _build_text_from_syndication(syndicated)
                if text:
                    word_count = len(text.split())
                    log.info("tweet_extraction_complete", word_count=word_count, quality=0.95)
                    return ExtractedContent(
                        source=source,
                        title=tweet_id,
                        text=text,
                        author=author,
                        site_name="Twitter/X",
                        word_count=word_count,
                        extraction_quality=0.95,
                        warnings=warnings,
                    )

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

    if _is_javascript_gate_text(text):
        warnings.append(
            ExtractionWarning(
                code="javascript_required",
                message="X returned a JavaScript-required page; tweet text could not be extracted",
            )
        )
        fallback_title = (
            tweet_id or source.canonical_url.split("/")[-1] if "/" in source.canonical_url else "Tweet"
        )
        return ExtractedContent(
            source=source,
            title=fallback_title,
            text="",
            site_name="Twitter/X",
            word_count=0,
            extraction_quality=0.1,
            warnings=warnings,
        )

    title = tweet_id or source.canonical_url.split("/")[-1] if "/" in source.canonical_url else "Tweet"
    word_count = len(text.split()) if text else 0

    if not text:
        warnings.append(
            ExtractionWarning(code="empty_content", message="No text could be extracted")
        )

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
