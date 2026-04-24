"""MOC generation helpers for topic digest outputs."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from vaultmind.config import AppConfig
from vaultmind.core.writer import slugify, write_markdown_page

if TYPE_CHECKING:
    from vaultmind.ai.knowledge import TopicDigest
    from vaultmind.core.search import SearchMatch


AUTO_MOC_MIN_NOTES = 5


def get_moc_path(topic: str, config: AppConfig) -> Path:
    """Resolve the path for an auto-generated MOC file."""
    filename = f"{slugify(topic)}-moc.md"
    return config.vault_path / config.folders.mocs / filename


def should_generate_moc(topic: str, matches: Sequence[object], *, min_notes: int = 5) -> bool:
    """Return whether MOC generation should run for the digest."""
    return bool(topic.strip()) and len(matches) >= min_notes


def render_moc_markdown(topic: str, digest: TopicDigest, matches: Sequence[SearchMatch]) -> str:
    """Render the markdown body for a MOC page."""
    lines: list[str] = [f"# {topic} MOC", ""]

    lines.append("## Thesis")
    lines.append(digest.thesis)
    lines.append("")

    if digest.patterns:
        lines.append("## Patterns")
        for pattern in digest.patterns:
            lines.append(f"- {pattern}")
        lines.append("")

    if digest.tensions:
        lines.append("## Tensions")
        for tension in digest.tensions:
            lines.append(f"- {tension}")
        lines.append("")

    if digest.open_questions:
        lines.append("## Open Questions")
        for question in digest.open_questions:
            lines.append(f"- {question}")
        lines.append("")

    if digest.moc_sections:
        for section in digest.moc_sections:
            lines.append(f"## {section.heading}")
            if section.summary:
                lines.append(section.summary)
            for path in section.note_paths:
                lines.append(f"- [[{path}]]")
            lines.append("")

    lines.append("## Notes")
    for match in matches:
        lines.append(f"- [[{match.note.relative_path}|{match.note.title}]]")
    lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_moc(
    topic: str,
    digest: TopicDigest,
    matches: Sequence[SearchMatch],
    config: AppConfig,
) -> Path:
    """Write a generated MOC page to the vault."""
    path = get_moc_path(topic, config)
    body = render_moc_markdown(topic, digest, matches)
    now = datetime.now(UTC).isoformat()

    frontmatter = {
        "title": f"{topic} MOC",
        "vaultmind": True,
        "kind": "moc",
        "topic": topic,
        "generated_by": "vm digest",
        "updated": now,
        "note_count": len(matches),
        "tags": ["moc", slugify(topic)],
    }

    return write_markdown_page(path, body=body, frontmatter=frontmatter)
