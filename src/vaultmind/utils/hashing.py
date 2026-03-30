"""Content hashing for duplicate detection."""

from __future__ import annotations

import hashlib
import unicodedata


def content_hash(text: str) -> str:
    """Generate a short hash of content for dedup. Returns first 8 hex chars of SHA-256."""
    normalized = unicodedata.normalize("NFC", text.strip().lower())
    return hashlib.sha256(normalized.encode()).hexdigest()[:8]
