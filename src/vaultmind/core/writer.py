"""Vault writer — atomic file writes to Obsidian vault."""

from __future__ import annotations

import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

import structlog
import yaml

from vaultmind.config import AppConfig
from vaultmind.schemas import (
    ArticleCategory,
    NoteFrontmatter,
    RenderedNote,
    SourceType,
)

log = structlog.get_logger()

MAX_FILENAME_LENGTH = 80


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug."""
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()
    # Remove emoji and special characters
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    text = text.strip("-")
    return text[:MAX_FILENAME_LENGTH] if text else "untitled"


def generate_filename(title: str, content_hash: str = "") -> str:
    """Generate a deterministic, filesystem-safe filename.

    Collision is handled at write time via generate_filename_with_hash().
    """
    slug = slugify(title)
    return f"{slug}.md"


def generate_filename_with_hash(title: str, content_hash: str) -> str:
    """Generate filename with content hash suffix for collision resolution."""
    slug = slugify(title)
    return f"{slug}--{content_hash}.md"


def resolve_folder(
    source_type: SourceType,
    category: ArticleCategory,
    config: AppConfig,
) -> Path:
    """Determine the target folder based on source type and category."""
    vault = config.vault_path

    if source_type == SourceType.ARTICLE:
        base = vault / config.folders.articles
        return base / category.value

    if source_type == SourceType.GITHUB:
        return vault / config.folders.tools

    if source_type == SourceType.REDDIT:
        return vault / config.folders.discussions

    if source_type == SourceType.TWEET:
        return vault / config.folders.threads

    return vault / config.folders.inbox


def render_frontmatter(fm: NoteFrontmatter) -> str:
    """Render frontmatter as YAML string."""
    data = {
        "title": fm.title,
        "source": fm.source,
        "canonical_url": fm.canonical_url,
        "type": fm.type.value,
        "author": fm.author,
        "saved": fm.saved.isoformat(),
        "tags": fm.tags,
        "rating": fm.rating,
        "read_time_minutes": fm.read_time_minutes,
        "status": fm.status.value,
        "content_hash": fm.content_hash,
        "model_used": fm.model_used,
        "extraction_quality": fm.extraction_quality,
        "vaultmind": fm.vaultmind,
    }
    # Source-specific fields
    if fm.subreddit:
        data["subreddit"] = fm.subreddit
    if fm.repo_name:
        data["repo_name"] = fm.repo_name
    if fm.language:
        data["language"] = fm.language
    if fm.stars is not None:
        data["stars"] = fm.stars
    if fm.last_updated:
        data["last_updated"] = fm.last_updated

    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def write_note(note: RenderedNote, config: AppConfig) -> Path:
    """Atomically write a rendered note to the vault.

    Returns the path to the written file.
    """
    folder = Path(note.folder_path)
    folder.mkdir(parents=True, exist_ok=True)

    target = folder / note.filename

    # Handle filename collision
    if target.exists():
        target = folder / generate_filename_with_hash(
            note.frontmatter.title, note.frontmatter.content_hash
        )

    frontmatter_str = render_frontmatter(note.frontmatter)
    content = f"---\n{frontmatter_str}---\n\n{note.body}"

    # Atomic write: write to temp file, then rename
    fd, tmp_path = tempfile.mkstemp(dir=folder, suffix=".md.tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(tmp_path).replace(target)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    log.info("note_written", path=str(target))
    return target


def write_markdown_page(
    path: Path,
    *,
    body: str,
    frontmatter: dict[str, Any] | None = None,
) -> Path:
    """Atomically write a generic markdown page with optional frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)

    content_body = body.rstrip() + "\n"
    if frontmatter is not None:
        fm = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
        content = f"---\n{fm}---\n\n{content_body}"
    else:
        content = content_body

    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".md.tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(tmp_path).replace(path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    log.info("markdown_page_written", path=str(path))
    return path


def parse_frontmatter(file_path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from a markdown file. Returns None on failure."""
    try:
        text = file_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None
        end = text.find("---", 3)
        if end == -1:
            return None
        fm_data = yaml.safe_load(text[3:end])
        return fm_data if isinstance(fm_data, dict) else None
    except (OSError, yaml.YAMLError):
        return None


def find_existing_note(canonical_url: str, config: AppConfig) -> Path | None:
    """Check if a note with this canonical URL already exists in the vault."""
    for md_file in config.vault_path.rglob("*.md"):
        fm = parse_frontmatter(md_file)
        if fm and fm.get("canonical_url") == canonical_url:
            return md_file
    return None
