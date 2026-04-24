"""GitHub repo extraction via the GitHub REST API."""

from __future__ import annotations

from typing import Any, cast
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
    GitHubRepoMetadata,
)

log = structlog.get_logger()

_API_BASE = "https://api.github.com"


class GitHubAPIError(Exception):
    """Raised on retryable GitHub API failures (429 / 5xx)."""


def _parse_owner_repo(canonical_url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL path."""
    path = urlparse(canonical_url).path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Cannot parse owner/repo from URL: {canonical_url}")
    return parts[0], parts[1]


def _build_headers(config: AppConfig) -> dict[str, str]:
    """Build request headers, including auth token if available."""
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "VaultMind/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = config.env.github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


@retry(
    retry=retry_if_exception_type(GitHubAPIError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _fetch_repo(owner: str, repo: str, headers: dict[str, str]) -> dict[str, Any]:
    """Fetch repository metadata from the GitHub REST API."""
    url = f"{_API_BASE}/repos/{owner}/{repo}"
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=20.0) as client:
        resp = await client.get(url)
    if resp.status_code == 429 or resp.status_code >= 500:
        raise GitHubAPIError(f"GitHub returned {resp.status_code}")
    resp.raise_for_status()
    return cast(dict[str, Any], resp.json())


@retry(
    retry=retry_if_exception_type(GitHubAPIError),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _fetch_readme(owner: str, repo: str, headers: dict[str, str]) -> str | None:
    """Fetch the raw README content. Returns None if not found."""
    url = f"{_API_BASE}/repos/{owner}/{repo}/readme"
    readme_headers = {**headers, "Accept": "application/vnd.github.raw+json"}
    async with httpx.AsyncClient(
        headers=readme_headers,
        follow_redirects=True,
        timeout=20.0,
    ) as client:
        resp = await client.get(url)
    if resp.status_code == 404:
        return None
    if resp.status_code == 429 or resp.status_code >= 500:
        raise GitHubAPIError(f"GitHub returned {resp.status_code}")
    resp.raise_for_status()
    return resp.text


def _build_text(description: str | None, readme: str | None) -> str:
    """Combine repo description and README into a single text block."""
    parts: list[str] = []
    if description:
        parts.append(description)
    if readme:
        parts.append(readme)
    return "\n\n".join(parts)


async def extract_github(source: CanonicalSource, config: AppConfig) -> ExtractedContent:
    """Extract content from a GitHub repository URL.

    Fetches repo metadata and README via the GitHub REST API and returns
    an ``ExtractedContent`` with ``GitHubRepoMetadata``.
    """
    log.info("extracting_github", url=source.canonical_url)
    warnings: list[ExtractionWarning] = []
    quality = 1.0

    try:
        owner, repo_name = _parse_owner_repo(source.canonical_url)
    except ValueError as exc:
        log.error("github_parse_failed", url=source.canonical_url, error=str(exc))
        return ExtractedContent(
            source=source,
            title=source.canonical_url,
            text="",
            extraction_quality=0.1,
            warnings=[ExtractionWarning(code="parse_failed", message=str(exc))],
        )

    headers = _build_headers(config)

    # Fetch repo metadata
    try:
        repo_data = await _fetch_repo(owner, repo_name, headers)
    except Exception as exc:
        log.error("github_repo_fetch_failed", url=source.canonical_url, error=str(exc))
        return ExtractedContent(
            source=source,
            title=f"{owner}/{repo_name}",
            text="",
            extraction_quality=0.2,
            warnings=[ExtractionWarning(code="fetch_failed", message=str(exc))],
        )

    # Fetch README
    readme: str | None = None
    try:
        readme = await _fetch_readme(owner, repo_name, headers)
    except Exception as exc:
        log.warning("github_readme_fetch_failed", owner=owner, repo=repo_name, error=str(exc))
        warnings.append(ExtractionWarning(code="readme_missing", message=str(exc)))
        quality = min(quality, 0.7)

    if readme is None:
        msg = "Repository has no README"
        warnings.append(ExtractionWarning(code="readme_missing", message=msg))
        quality = min(quality, 0.7)

    description = repo_data.get("description")
    license_info = repo_data.get("license") or {}
    license_name = license_info.get("spdx_id") if isinstance(license_info, dict) else None

    text = _build_text(description, readme)
    word_count = len(text.split()) if text else 0

    metadata = GitHubRepoMetadata(
        owner=owner,
        repo=repo_name,
        description=description,
        language=repo_data.get("language"),
        stars=repo_data.get("stargazers_count"),
        forks=repo_data.get("forks_count"),
        open_issues=repo_data.get("open_issues_count"),
        license=license_name,
        homepage=repo_data.get("homepage") or None,
        topics=repo_data.get("topics", []),
        last_pushed_at=repo_data.get("pushed_at"),
    )

    title = repo_data.get("full_name", f"{owner}/{repo_name}")

    log.info(
        "github_extraction_complete",
        title=title,
        word_count=word_count,
        stars=metadata.stars,
        quality=quality,
    )

    return ExtractedContent(
        source=source,
        title=title,
        text=text,
        author=owner,
        site_name="GitHub",
        word_count=word_count,
        source_metadata=metadata,
        warnings=warnings,
        extraction_quality=quality,
    )
