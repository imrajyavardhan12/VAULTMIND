"""Related-note finder for vault intelligence linking."""

from __future__ import annotations

import re

from vaultmind.config import AppConfig
from vaultmind.core.writer import parse_frontmatter
from vaultmind.schemas import RelatedNoteMatch

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "what",
    "when",
    "why",
    "with",
}


def _jaccard(a: set[str], b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _normalize_tags(tags: object) -> set[str]:
    """Normalize a frontmatter tags value into a lowercase set."""
    if not isinstance(tags, list):
        return set()

    normalized: set[str] = set()
    for tag in tags:
        if not isinstance(tag, str):
            continue
        clean = tag.strip().lower()
        if clean:
            normalized.add(clean)
    return normalized


def _tokenize_title(title: str) -> set[str]:
    """Tokenize and normalize note titles for overlap scoring."""
    tokens = re.findall(r"[a-z0-9]+", title.lower())
    return {token for token in tokens if len(token) >= 2 and token not in STOPWORDS}


def find_related_notes(
    *,
    current_title: str,
    current_tags: list[str],
    current_canonical_url: str,
    config: AppConfig,
    limit: int = 5,
    min_score: float = 0.15,
) -> list[RelatedNoteMatch]:
    """Find related vault notes using weighted Jaccard similarity."""
    if limit <= 0:
        return []

    vault_path = config.vault_path
    if not vault_path.exists():
        return []

    current_tag_set = _normalize_tags(current_tags)
    current_title_tokens = _tokenize_title(current_title)

    matches: list[RelatedNoteMatch] = []

    for file_path in vault_path.rglob("*.md"):
        frontmatter = parse_frontmatter(file_path)
        if not frontmatter:
            continue

        if frontmatter.get("vaultmind") is not True:
            continue

        candidate_canonical = frontmatter.get("canonical_url")
        if isinstance(candidate_canonical, str) and candidate_canonical == current_canonical_url:
            continue

        raw_title = frontmatter.get("title")
        title = raw_title.strip() if isinstance(raw_title, str) else file_path.stem
        if not title:
            title = file_path.stem

        candidate_tags = _normalize_tags(frontmatter.get("tags"))
        candidate_title_tokens = _tokenize_title(title)

        shared_tags = sorted(current_tag_set & candidate_tags)
        shared_title_tokens = current_title_tokens & candidate_title_tokens
        if not shared_tags and not shared_title_tokens:
            continue

        tag_score = _jaccard(current_tag_set, candidate_tags)
        title_score = _jaccard(current_title_tokens, candidate_title_tokens)
        total_score = (0.7 * tag_score) + (0.3 * title_score)

        if total_score < min_score:
            continue

        try:
            relative_path = file_path.relative_to(vault_path).with_suffix("").as_posix()
        except ValueError:
            continue

        matches.append(
            RelatedNoteMatch(
                title=title,
                path=relative_path,
                score=total_score,
                shared_tags=shared_tags,
            )
        )

    matches.sort(key=lambda match: (-match.score, -len(match.shared_tags), match.title.lower()))
    return matches[:limit]
