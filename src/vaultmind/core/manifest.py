"""Vault manifest — source of truth for the compile loop.

vault.manifest.json lives at the vault root. It tracks:
- Which sources have been compiled
- Which wiki articles exist and what sources they came from
- Content hashes to detect changes

This is what makes vm compile incremental instead of a full rebuild.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from vaultmind.schemas import Manifest, ManifestSource, ManifestWikiEntry

MANIFEST_FILENAME = "vault.manifest.json"


def manifest_path(vault_path: Path) -> Path:
    return vault_path / MANIFEST_FILENAME


def read_manifest(vault_path: Path) -> Manifest:
    """Load the manifest from disk. Returns empty Manifest if file doesn't exist."""
    path = manifest_path(vault_path)
    if not path.exists():
        return Manifest()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Manifest.model_validate(data)
    except (OSError, json.JSONDecodeError):
        return Manifest()


def write_manifest(vault_path: Path, manifest: Manifest) -> None:
    """Write the manifest to disk atomically."""
    path = manifest_path(vault_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write: temp file + rename
    tmp = path.with_suffix(".json.tmp")
    try:
        tmp.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def upsert_source(
    manifest: Manifest,
    *,
    url: str,
    content_hash: str,
    saved_at: datetime,
    wiki_articles: list[str] | None = None,
) -> None:
    """Add or update a source entry in the manifest."""
    now = datetime.now(UTC)
    existing = manifest.sources.get(url)

    if existing is not None:
        manifest.sources[url] = ManifestSource(
            content_hash=content_hash,
            saved_at=existing.saved_at,
            compiled_at=now,
            wiki_articles=wiki_articles if wiki_articles is not None else existing.wiki_articles,
        )
    else:
        manifest.sources[url] = ManifestSource(
            content_hash=content_hash,
            saved_at=saved_at,
            compiled_at=now,
            wiki_articles=wiki_articles or [],
        )


def upsert_wiki_article(
    manifest: Manifest,
    *,
    slug: str,
    content_hash: str,
    source_urls: list[str],
) -> None:
    """Add or update a wiki article entry in the manifest."""
    manifest.wiki_articles[slug] = ManifestWikiEntry(
        last_updated=datetime.now(UTC),
        source_urls=source_urls,
        content_hash=content_hash,
    )


def is_source_new_or_changed(
    manifest: Manifest,
    url: str,
    current_hash: str,
) -> bool:
    """Return True if the source is new or its content hash has changed."""
    existing = manifest.sources.get(url)
    if existing is None:
        return True
    return existing.content_hash != current_hash


def get_changed_sources(
    manifest: Manifest,
    source_hashes: dict[str, str],
) -> list[str]:
    """Return list of source URLs that are new or have changed content hashes."""
    changed = []
    for url, current_hash in source_hashes.items():
        if is_source_new_or_changed(manifest, url, current_hash):
            changed.append(url)
    return changed


def update_compiled_at(manifest: Manifest) -> None:
    """Update the last_compiled timestamp."""
    manifest.last_compiled = datetime.now(UTC)
