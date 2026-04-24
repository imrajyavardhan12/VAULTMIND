"""Scanner for raw markdown sources from Obsidian Web Clipper.

These are immutable original source documents — the LLM reads them but never modifies them.
This is the source of truth for vm compile.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from vaultmind.config import AppConfig
from vaultmind.utils.hashing import content_hash

log = structlog.get_logger()


@dataclass(slots=True)
class RawSourceRecord:
    """A raw source document scanned from the Raw/ folder."""

    path: Path
    relative_path: str  # vault-relative, no .md, posix
    title: str
    source_url: str | None  # from frontmatter source field
    body: str  # markdown body without frontmatter
    content_hash: str
    raw_tags: list[str]  # from frontmatter tags


def scan_raw_sources(config: AppConfig) -> list[RawSourceRecord]:
    """Scan the raw/ folder for markdown source documents."""
    raw_path = _resolve_raw_path(config)
    if not raw_path.exists():
        log.info("raw_folder_missing", path=str(raw_path))
        return []

    records: list[RawSourceRecord] = []
    for md_file in raw_path.rglob("*.md"):
        record = _parse_raw_file(md_file, config.vault_path)
        if record:
            records.append(record)

    log.info("raw_sources_scanned", count=len(records), path=str(raw_path))
    return sorted(records, key=lambda r: r.path.name.lower())


def _resolve_raw_path(config: AppConfig) -> Path:
    """Resolve the configured raw folder, with a legacy Clippings fallback.

    Older VaultMind configs and some Obsidian Web Clipper setups used
    ``Clippings``. New configs use the product-facing ``📥 Raw`` name, but
    existing vaults should keep compiling without a migration step.
    """
    raw_path = config.vault_path / config.folders.raw
    if raw_path.exists() or config.folders.raw != "📥 Raw":
        return raw_path

    legacy_path = config.vault_path / "Clippings"
    if legacy_path.exists():
        log.info("raw_folder_legacy_fallback", configured=str(raw_path), fallback=str(legacy_path))
        return legacy_path

    return raw_path


def _parse_raw_file(file_path: Path, vault_path: Path) -> RawSourceRecord | None:
    """Parse a raw markdown file into a RawSourceRecord."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        log.warning("raw_file_read_error", path=str(file_path), error=str(exc))
        return None

    # Split frontmatter from body
    if text.startswith("---"):
        end = text.find("---", 3)
        if end == -1:
            fm_text = ""
            body = text
        else:
            fm_text = text[3:end]
            body = text[end + 3:]
    else:
        fm_text = ""
        body = text

    body = body.strip()

    # Parse frontmatter
    frontmatter = _parse_frontmatter(fm_text)

    # Extract title
    title = _extract_title(body) or file_path.stem

    # Get source URL
    source_url = frontmatter.get("source") or frontmatter.get("canonical_url")

    # Get tags
    raw_tags = _parse_tags(frontmatter.get("tags"))

    # Content hash is of the body only (not frontmatter)
    c_hash = content_hash(body)

    try:
        relative_path = file_path.relative_to(vault_path).with_suffix("").as_posix()
    except ValueError:
        relative_path = file_path.name

    return RawSourceRecord(
        path=file_path,
        relative_path=relative_path,
        title=title,
        source_url=source_url if isinstance(source_url, str) else None,
        body=body,
        content_hash=c_hash,
        raw_tags=raw_tags,
    )


def _parse_frontmatter(fm_text: str) -> dict[str, Any]:
    """Parse YAML frontmatter text into a dict."""
    if not fm_text.strip():
        return {}

    try:
        import yaml
        data = yaml.safe_load(fm_text)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError as exc:
        log.warning("frontmatter_parse_error", error=str(exc))
        return {}


def _extract_title(body: str) -> str | None:
    """Extract title from the first # heading in the body."""
    if not body:
        return None
    match = re.search(r"^#\s+(.+?)$", body, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def _parse_tags(value: object) -> list[str]:
    """Parse frontmatter tags into a list of strings."""
    if isinstance(value, list):
        return [str(t).strip().lower() for t in value if t]
    if isinstance(value, str):
        return [t.strip().lower() for t in value.split(",") if t.strip()]
    return []


def _strip_broken_images(text: str) -> str:
    """Remove images from CDNs that don't support hotlinking (return 404 when embedded)."""
    import re

    # Substack uses session tokens that expire — these URLs always return 404 when hotlinked
    # Match markdown images with URLs from substackcdn.com or substack-post-media.s3.amazonaws.com
    pattern = r'!\[[^\]]*\]\(https?://(?:substackcdn\.com|substack-post-media\.s3\.amazonaws\.com)[^)]*\)'
    return re.sub(pattern, '', text)


def format_raw_source_packet(record: RawSourceRecord, *, max_chars: int = 8000) -> str:
    """Format a raw source record for the LLM triage prompt.

    Includes the actual original content, not AI summaries.
    """
    title = record.title
    source = record.source_url or record.relative_path
    tags = ", ".join(record.raw_tags) if record.raw_tags else "none"

    # Strip broken CDN images before passing to LLM
    body = _strip_broken_images(record.body)
    if len(body) > max_chars:
        body = body[:max_chars].rstrip() + "\n\n[Content truncated]"

    return (
        f"Title: {title}\n"
        f"Source: {source}\n"
        f"Tags: {tags}\n\n"
        f"---\n\n"
        f"{body}"
    )
