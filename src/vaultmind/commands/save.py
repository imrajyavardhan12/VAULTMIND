"""vm save — the core command. Process any URL and save to vault."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import structlog

from vaultmind.ai.pipeline import generate_flashcards, process_content
from vaultmind.ai.providers import get_provider
from vaultmind.config import AppConfig
from vaultmind.core.extractors import extract_source
from vaultmind.core.linker import find_related_notes
from vaultmind.core.renderers import append_note_sections, render_note_body
from vaultmind.core.router import route_url
from vaultmind.core.writer import (
    find_existing_note,
    generate_filename,
    resolve_folder,
    write_note,
)
from vaultmind.schemas import (
    GitHubRepoMetadata,
    NoteFrontmatter,
    NoteStatus,
    RedditMetadata,
    RenderedNote,
    SourceType,
)
from vaultmind.utils.display import get_progress, print_error, print_success, print_warning
from vaultmind.utils.hashing import content_hash

log = structlog.get_logger()


def save_url(
    url: str,
    config: AppConfig,
    tags: list[str] | None = None,
    folder: str | None = None,
    force: bool = False,
    no_flash: bool = False,
) -> None:
    """Process a URL and save it to the vault. Sync wrapper for the async pipeline."""
    asyncio.run(_save_url_async(url, config, tags, folder, force, no_flash))


async def _save_url_async(
    url: str,
    config: AppConfig,
    tags: list[str] | None = None,
    folder: str | None = None,
    force: bool = False,
    no_flash: bool = False,
) -> None:
    """Async implementation of the save pipeline."""
    with get_progress() as progress:
        # Step 1: Route URL
        task = progress.add_task("Analyzing URL...", total=None)
        source = route_url(url)

        if source.source_type == SourceType.UNKNOWN:
            print_error(f"Unsupported URL type: {url}")
            return

        # Step 2: Check for duplicates
        progress.update(task, description="Checking for duplicates...")
        existing = find_existing_note(source.canonical_url, config)
        if existing and not force:
            if tags:
                _merge_tags(existing, tags)
                print_success(
                    "Tags Merged",
                    f"Added tags {tags} to existing note:\n{existing}",
                )
            else:
                print_warning(f"Already saved: {existing}\nUse --force to re-process.")
            return

        # Step 3: Extract content
        progress.update(task, description="Extracting content...")
        content = await extract_source(source, config)

        if not content.text:
            print_error("Failed to extract content from URL. The page may be paywalled or empty.")
            return

        # Print extraction warnings
        for warning in content.warnings:
            print_warning(f"[{warning.code}] {warning.message}")

        # Step 4: AI processing
        progress.update(task, description="Processing with AI...")
        provider = get_provider(config, tier="fast")
        enrichment = await process_content(content, provider)

        # Step 5: Build note
        progress.update(task, description="Building note...")
        c_hash = content_hash(content.text)

        extra_tags = tags or []
        all_tags = list(dict.fromkeys(enrichment.tags + extra_tags))

        # Build source-specific frontmatter fields
        fm_kwargs = _build_frontmatter_kwargs(content, source, enrichment, c_hash, provider, all_tags)
        frontmatter = NoteFrontmatter(**fm_kwargs)

        should_generate = config.ai.generate_flashcards and not no_flash
        flashcards = (
            await generate_flashcards(content, enrichment, provider) if should_generate else []
        )
        related_notes = find_related_notes(
            current_title=content.title,
            current_tags=all_tags,
            current_canonical_url=source.canonical_url,
            config=config,
        )

        body = render_note_body(content, enrichment)
        body = append_note_sections(body, flashcards=flashcards, related_notes=related_notes)

        # Resolve folder
        if folder:
            target_folder = config.vault_path / folder
            if not str(target_folder.resolve()).startswith(str(config.vault_path.resolve())):
                print_error(f"Invalid folder: {folder}. Must be under vault root.")
                return
            folder_path = str(target_folder)
        else:
            folder_path = str(resolve_folder(source.source_type, enrichment.category, config))

        filename = generate_filename(content.title, c_hash)

        note = RenderedNote(
            frontmatter=frontmatter,
            body=body,
            filename=filename,
            folder_path=folder_path,
        )

        # Step 6: Write to vault
        progress.update(task, description="Writing to vault...")
        written_path = write_note(note, config)

    print_success(
        f"Saved: {content.title}",
        f"📁 {written_path}\n"
        f"📂 Category: {enrichment.category.value}\n"
        f"🏷️  Tags: {', '.join(all_tags)}\n"
        f"⭐ Rating: {enrichment.rating}/10\n"
        f"📖 Read time: {enrichment.read_time_minutes} min",
    )


def _build_frontmatter_kwargs(content, source, enrichment, c_hash, provider, all_tags) -> dict:
    """Build frontmatter kwargs, including source-specific fields."""
    kwargs: dict = {
        "title": content.title,
        "source": source.original_url,
        "canonical_url": source.canonical_url,
        "type": source.source_type,
        "author": content.author,
        "saved": datetime.now(timezone.utc),
        "tags": all_tags,
        "rating": enrichment.rating,
        "read_time_minutes": enrichment.read_time_minutes,
        "status": NoteStatus.PROCESSED if content.extraction_quality >= 0.5 else NoteStatus.PARTIAL,
        "content_hash": c_hash,
        "model_used": provider.model,
        "extraction_quality": content.extraction_quality,
    }

    # Reddit-specific
    meta = content.source_metadata
    if isinstance(meta, RedditMetadata):
        kwargs["subreddit"] = meta.subreddit

    # GitHub-specific
    if isinstance(meta, GitHubRepoMetadata):
        kwargs["repo_name"] = f"{meta.owner}/{meta.repo}"
        kwargs["language"] = meta.language
        kwargs["stars"] = meta.stars
        kwargs["last_updated"] = meta.last_pushed_at[:10] if meta.last_pushed_at else None

    return kwargs


def _merge_tags(note_path: Path, new_tags: list[str]) -> None:
    """Merge new tags into an existing note's frontmatter."""
    import yaml

    text = note_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return

    end = text.find("---", 3)
    if end == -1:
        return

    fm_text = text[3:end]
    body = text[end + 3:]

    try:
        fm_data = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return

    if not isinstance(fm_data, dict):
        return

    existing_tags = fm_data.get("tags", [])
    merged = list(dict.fromkeys(existing_tags + new_tags))
    fm_data["tags"] = merged

    new_fm = yaml.dump(fm_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    note_path.write_text(f"---\n{new_fm}---{body}", encoding="utf-8")
