"""Tag normalization helpers for Obsidian-compatible metadata."""

from __future__ import annotations

import re
import unicodedata


def normalize_tag(tag: str) -> str:
    """Normalize a single tag to a filesystem/Obsidian-safe shape.

    Rules:
    - lowercase
    - strip leading '#'
    - whitespace/underscore collapsed to '-'
    - punctuation removed
    - preserve nested tag separators via '/'
    """
    text = unicodedata.normalize("NFC", tag).strip().lower()
    text = text.lstrip("#").strip()
    if not text:
        return ""

    segments: list[str] = []
    for segment in text.split("/"):
        normalized = segment.replace("_", " ")
        normalized = re.sub(r"[^\w\s-]", " ", normalized)
        normalized = re.sub(r"[-\s]+", "-", normalized)
        normalized = normalized.strip("-")
        if normalized:
            segments.append(normalized)

    return "/".join(segments)


def normalize_tags(tags: list[str]) -> list[str]:
    """Normalize and dedupe tags while preserving first-seen order."""
    out: list[str] = []
    for raw in tags:
        clean = normalize_tag(raw)
        if clean and clean not in out:
            out.append(clean)
    return out
