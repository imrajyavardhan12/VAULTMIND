"""Reddit content extraction via the Reddit JSON API."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from vaultmind.config import AppConfig
from vaultmind.schemas import (
    CanonicalSource,
    ExtractedContent,
    ExtractionWarning,
    RedditComment,
    RedditMetadata,
)

log = structlog.get_logger()

_USER_AGENT = "VaultMind/1.0"
_MAX_TOP_COMMENTS = 5


class RedditAPIError(Exception):
    """Raised on retryable Reddit API failures (429 / 5xx)."""


@retry(
    retry=retry_if_exception_type(RedditAPIError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _fetch_json(url: str) -> dict:
    """Fetch a Reddit JSON endpoint with retry on 429 / 5xx."""
    json_url = url.rstrip("/") + ".json"
    async with httpx.AsyncClient(
        headers={"User-Agent": _USER_AGENT},
        follow_redirects=True,
        timeout=20.0,
    ) as client:
        resp = await client.get(json_url)

    if resp.status_code == 429 or resp.status_code >= 500:
        raise RedditAPIError(f"Reddit returned {resp.status_code}")
    resp.raise_for_status()
    return resp.json()


def _parse_comments(comment_listing: dict) -> list[RedditComment]:
    """Extract the top comments from the comment listing."""
    comments: list[RedditComment] = []
    children = comment_listing.get("data", {}).get("children", [])
    for child in children:
        if child.get("kind") != "t1":
            continue
        data = child.get("data", {})
        body = data.get("body", "")
        if not body or body == "[deleted]":
            continue
        comments.append(
            RedditComment(
                author=data.get("author") or None,
                body=body,
                score=data.get("score"),
                permalink=data.get("permalink"),
            )
        )
        if len(comments) >= _MAX_TOP_COMMENTS:
            break
    return comments


def _build_text(title: str, selftext: str, comments: list[RedditComment]) -> str:
    """Flatten post + top comments into a single text block for AI."""
    parts: list[str] = [f"# {title}"]
    if selftext:
        parts.append(selftext)
    if comments:
        parts.append("--- TOP COMMENTS ---")
        for i, c in enumerate(comments, 1):
            author = c.author or "[deleted]"
            parts.append(f"Comment {i} (u/{author}, score {c.score}):\n{c.body}")
    return "\n\n".join(parts)


async def extract_reddit(source: CanonicalSource, config: AppConfig) -> ExtractedContent:
    """Extract content from a Reddit post URL.

    Fetches the post and its top comments via the Reddit JSON API and
    returns an ``ExtractedContent`` with ``RedditMetadata``.
    """
    log.info("extracting_reddit", url=source.canonical_url)
    warnings: list[ExtractionWarning] = []
    quality = 1.0

    try:
        data = await _fetch_json(source.canonical_url)
    except Exception as exc:
        log.error("reddit_fetch_failed", url=source.canonical_url, error=str(exc))
        return ExtractedContent(
            source=source,
            title=source.canonical_url,
            text="",
            extraction_quality=0.2,
            warnings=[ExtractionWarning(code="fetch_failed", message=str(exc))],
        )

    # Reddit returns a list: [post_listing, comment_listing]
    if not isinstance(data, list) or len(data) < 2:
        log.warning("reddit_unexpected_format", url=source.canonical_url)
        return ExtractedContent(
            source=source,
            title=source.canonical_url,
            text="",
            extraction_quality=0.2,
            warnings=[ExtractionWarning(code="unexpected_format", message="Unexpected Reddit JSON structure")],
        )

    post_data = data[0].get("data", {}).get("children", [{}])[0].get("data", {})

    title = post_data.get("title", "Untitled Reddit Post")
    selftext = post_data.get("selftext", "")
    author = post_data.get("author") or None
    subreddit = post_data.get("subreddit", "unknown")
    score = post_data.get("score")
    num_comments = post_data.get("num_comments")

    # Handle deleted posts
    if selftext == "[deleted]" or selftext == "[removed]":
        warnings.append(ExtractionWarning(code="deleted_post", message=f"Post content is {selftext}"))
        selftext = ""
        quality = min(quality, 0.5)

    # Parse comments
    comments = _parse_comments(data[1])
    if not comments and not selftext:
        warnings.append(ExtractionWarning(code="no_content", message="No selftext or comments available"))
        quality = min(quality, 0.3)

    text = _build_text(title, selftext, comments)
    word_count = len(text.split()) if text else 0

    metadata = RedditMetadata(
        subreddit=subreddit,
        post_author=author,
        score=score,
        num_comments=num_comments,
        top_comments=comments,
        sort="best",
    )

    log.info(
        "reddit_extraction_complete",
        title=title,
        subreddit=subreddit,
        word_count=word_count,
        comment_count=len(comments),
        quality=quality,
    )

    return ExtractedContent(
        source=source,
        title=title,
        text=text,
        author=author,
        site_name=f"r/{subreddit}",
        word_count=word_count,
        source_metadata=metadata,
        warnings=warnings,
        extraction_quality=quality,
    )
