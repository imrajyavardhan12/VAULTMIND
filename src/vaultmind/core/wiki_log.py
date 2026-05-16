"""Append-only wiki activity log helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from vaultmind.config import AppConfig

LOG_FILENAME = "📋 Log.md"


def wiki_log_path(config: AppConfig) -> Path:
    """Return the canonical Wiki log path."""
    return config.vault_path / config.folders.wiki / LOG_FILENAME


def append_wiki_log(config: AppConfig, *, event: str, detail: str, when: datetime | None = None) -> Path:
    """Append a dated event to the wiki log."""
    now = when or datetime.now(UTC)
    path = wiki_log_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = path.read_text(encoding="utf-8") if path.exists() else "# Wiki Log\n"
    if not existing.endswith("\n"):
        existing += "\n"

    entry = f"\n## [{now.date().isoformat()}] {event} | {detail.strip()}\n"
    path.write_text(existing + entry, encoding="utf-8")
    return path
