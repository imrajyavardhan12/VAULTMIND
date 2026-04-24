"""Vault scanning and indexing utilities shared by Phase 4 commands."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from vaultmind.config import AppConfig
from vaultmind.core.writer import parse_frontmatter


@dataclass(slots=True)
class VaultNoteRecord:
    path: Path
    relative_path: str
    title: str
    saved_at: datetime | None
    tags: list[str]
    source_type: str | None
    rating: int | None
    read_time_minutes: int | None
    status: str | None
    canonical_url: str | None
    source: str | None
    vaultmind: bool
    body: str
    summary: str
    raw_frontmatter: dict[str, Any]


def scan_vault_notes(config: AppConfig, *, only_vaultmind: bool = True) -> list[VaultNoteRecord]:
    """Scan the vault and return indexed note records."""
    vault_path = config.vault_path
    if not vault_path.exists():
        return []

    records: list[VaultNoteRecord] = []
    for path in vault_path.rglob("*.md"):
        frontmatter = parse_frontmatter(path)
        if not frontmatter:
            continue

        vaultmind = frontmatter.get("vaultmind") is True
        if only_vaultmind and not vaultmind:
            continue

        body = read_markdown_body(path)
        summary = extract_summary_from_body(body)

        title_value = frontmatter.get("title")
        title = title_value.strip() if isinstance(title_value, str) else path.stem
        if not title:
            title = path.stem

        try:
            relative_path = path.relative_to(vault_path).with_suffix("").as_posix()
        except ValueError:
            continue

        _fm = frontmatter
        records.append(
            VaultNoteRecord(
                path=path,
                relative_path=relative_path,
                title=title,
                saved_at=parse_saved_at(_fm.get("saved")),
                tags=_normalize_tag_list(_fm.get("tags")),
                source_type=_fm.get("type") if isinstance(_fm.get("type"), str) else None,
                rating=_parse_optional_int(_fm.get("rating")),
                read_time_minutes=_parse_optional_int(_fm.get("read_time_minutes")),
                status=_fm.get("status") if isinstance(_fm.get("status"), str) else None,
                canonical_url=_fm.get("canonical_url") if isinstance(_fm.get("canonical_url"), str) else None,
                source=_fm.get("source") if isinstance(_fm.get("source"), str) else None,
                vaultmind=vaultmind,
                body=body,
                summary=summary,
                raw_frontmatter=frontmatter,
            )
        )

    return sorted(records, key=_record_sort_key, reverse=True)


def filter_notes_by_days(
    notes: list[VaultNoteRecord],
    *,
    days: int,
    now: datetime | None = None,
) -> list[VaultNoteRecord]:
    """Filter notes to those saved in the last N days."""
    if days <= 0:
        return []

    current = now or datetime.now(UTC)
    cutoff = current - timedelta(days=days)

    return [note for note in notes if note.saved_at is not None and note.saved_at >= cutoff]


def parse_saved_at(value: object) -> datetime | None:
    """Parse frontmatter `saved` values into timezone-aware datetimes."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def read_markdown_body(path: Path) -> str:
    """Read markdown body content without frontmatter."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text.strip()

    end = text.find("---", 3)
    if end == -1:
        return text.strip()

    return text[end + 3 :].strip()


def extract_summary_from_body(body: str) -> str:
    """Extract summary text from known summary headings or first paragraph fallback."""
    patterns = (
        r"^##\s*🧠\s*Summary\s*$",
        r"^##\s*🧠\s*Discussion Summary\s*$",
        r"^##\s*Summary\s*$",
    )

    for pattern in patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE | re.MULTILINE)
        if not match:
            continue

        remainder = body[match.end() :].lstrip()
        next_heading = re.search(r"^##\s+", remainder, flags=re.MULTILINE)
        block = remainder[: next_heading.start()] if next_heading else remainder
        summary = block.strip()
        if summary:
            return summary

    without_title = re.sub(r"^\s*#\s+.*\n+", "", body, count=1)
    for paragraph in re.split(r"\n\s*\n", without_title):
        cleaned = paragraph.strip()
        if cleaned and not cleaned.startswith("##"):
            return cleaned

    return ""


def truncate_for_ai(text: str, *, max_chars: int = 1200) -> str:
    """Truncate text payloads for AI prompts without splitting formatting too aggressively."""
    clean = text.strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def format_note_packet(note: VaultNoteRecord, *, max_chars: int = 1200) -> str:
    """Render a compact note packet for AI synthesis prompts."""
    saved_label = note.saved_at.isoformat() if note.saved_at else "unknown"
    tags_label = ", ".join(note.tags) if note.tags else "none"
    summary = truncate_for_ai(note.summary or note.body, max_chars=max_chars)
    canonical = note.canonical_url or note.relative_path

    return (
        f"Title: {note.title}\n"
        f"URL: {canonical}\n"
        f"Path: {note.relative_path}\n"
        f"Saved: {saved_label}\n"
        f"Tags: {tags_label}\n"
        f"Rating: {note.rating if note.rating is not None else 'unknown'}\n"
        f"Summary: {summary}"
    )


def _normalize_tag_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    tags: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        tag = item.strip().lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _parse_optional_int(value: object) -> int | None:
    if not isinstance(value, (int, float, str)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _record_sort_key(note: VaultNoteRecord) -> tuple[datetime, str]:
    fallback = datetime(1970, 1, 1, tzinfo=UTC)
    return note.saved_at or fallback, note.title.lower()
