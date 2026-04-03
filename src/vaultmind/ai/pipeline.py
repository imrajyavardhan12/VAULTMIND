"""Main AI processing pipeline.

Flow: ExtractedContent -> AIEnrichment
"""

from __future__ import annotations

import json

import structlog

from vaultmind.ai.json_utils import clean_json_response
from vaultmind.ai.providers.base import Provider
from vaultmind.ai.prompts import SYSTEM_PROMPT, build_flashcard_prompt, build_processing_prompt
from vaultmind.schemas import AIEnrichment, ArticleCategory, ExtractedContent, Flashcard

log = structlog.get_logger()

MAX_CONTENT_CHARS = 15000


async def process_content(content: ExtractedContent, provider: Provider) -> AIEnrichment:
    """Process extracted content through the AI pipeline."""
    log.info("pipeline_start", title=content.title, provider=provider.model)

    # Truncate content for token limits
    if len(content.text) > MAX_CONTENT_CHARS:
        original_text = content.text
        content = content.model_copy(
            update={"text": original_text[:MAX_CONTENT_CHARS] + "\n\n[Content truncated for processing]"}
        )
        log.info("content_truncated", original=len(original_text), truncated=MAX_CONTENT_CHARS)

    prompt = build_processing_prompt(content)

    raw_response = await provider.complete(prompt, system=SYSTEM_PROMPT)

    enrichment = _parse_ai_response(raw_response, content)
    log.info("pipeline_complete", title=content.title, rating=enrichment.rating)
    return enrichment


async def generate_flashcards(
    content: ExtractedContent,
    enrichment: AIEnrichment,
    provider: Provider,
) -> list[Flashcard]:
    """Generate 3-5 flashcards from extracted content and enrichment."""
    prompt = build_flashcard_prompt(content, enrichment)

    try:
        raw_response = await provider.complete(prompt, system=SYSTEM_PROMPT)
    except Exception as exc:
        log.warning("flashcard_generation_failed", title=content.title, error=str(exc))
        return []

    flashcards = _parse_flashcard_response(raw_response)
    log.info("flashcards_generated", title=content.title, count=len(flashcards))
    return flashcards


def _clean_json_response(response: str) -> str:
    """Compatibility wrapper for shared JSON cleanup utility."""
    return clean_json_response(response)


def _parse_ai_response(response: str, content: ExtractedContent) -> AIEnrichment:
    """Parse the AI JSON response into an AIEnrichment object."""
    cleaned = _clean_json_response(response)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        log.error("json_parse_failed", response=response[:200])
        return AIEnrichment(
            summary=f"Failed to process: {content.title}",
            key_ideas=["AI processing failed — review manually"],
            key_quotes=[],
            counterarguments=[],
            tags=["needs-review"],
            category=ArticleCategory.MISC,
            rating=5,
            read_time_minutes=max(1, content.word_count // 250),
        )

    raw_category = data.get("category", "Misc")
    try:
        category = ArticleCategory(raw_category)
    except ValueError:
        category = ArticleCategory.MISC

    rating = _safe_int(data.get("rating"), default=5)
    read_time = _safe_int(data.get("read_time_minutes"), default=max(1, content.word_count // 250))

    return AIEnrichment(
        summary=data.get("summary", ""),
        key_ideas=data.get("key_ideas", []),
        key_quotes=data.get("key_quotes", []),
        counterarguments=data.get("counterarguments", []),
        tags=data.get("tags", []),
        category=category,
        rating=min(10, max(1, rating)),
        read_time_minutes=max(1, read_time),
    )


def _parse_flashcard_response(response: str) -> list[Flashcard]:
    """Parse a flashcard JSON response into validated Flashcard objects."""
    cleaned = _clean_json_response(response)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        log.warning("flashcard_json_parse_failed", response=response[:200])
        return []

    if not isinstance(data, dict):
        return []

    raw_flashcards = data.get("flashcards")
    if not isinstance(raw_flashcards, list):
        return []

    flashcards: list[Flashcard] = []
    for item in raw_flashcards:
        if not isinstance(item, dict):
            continue
        question = item.get("question")
        answer = item.get("answer")
        if not isinstance(question, str) or not isinstance(answer, str):
            continue

        question = question.strip()
        answer = answer.strip()
        if not question or not answer:
            continue

        flashcards.append(Flashcard(question=question, answer=answer))
        if len(flashcards) >= 5:
            break

    return flashcards


def _safe_int(value: object, default: int) -> int:
    """Convert unknown values to int with a safe default fallback."""
    if not isinstance(value, (int, float, str)):
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default
