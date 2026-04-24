"""Typed data models for the VaultMind pipeline.

Pipeline flow: URL -> CanonicalSource -> ExtractedContent -> AIEnrichment -> RenderedNote
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    ARTICLE = "article"
    REDDIT = "reddit"
    GITHUB = "github"
    TWEET = "tweet"
    VIDEO = "video"
    UNKNOWN = "unknown"


class NoteStatus(StrEnum):
    PROCESSED = "processed"
    PARTIAL = "partial"
    REVIEW = "review"
    ARCHIVED = "archived"


class ArticleCategory(StrEnum):
    AI = "AI"
    TECH = "Tech"
    PHILOSOPHY = "Philosophy"
    BUSINESS = "Business"
    SCIENCE = "Science"
    DESIGN = "Design"
    MISC = "Misc"


class CanonicalSource(BaseModel):
    """URL after canonicalization — the single source of truth for dedup."""

    original_url: str
    canonical_url: str
    source_type: SourceType


class ExtractionWarning(BaseModel):
    """Warning from extraction (rate limit, missing data, etc.)."""

    code: str
    message: str


class RedditComment(BaseModel):
    """A single Reddit comment."""

    author: str | None = None
    body: str
    score: int | None = None
    permalink: str | None = None


class RedditMetadata(BaseModel):
    """Reddit-specific metadata."""

    subreddit: str
    post_author: str | None = None
    score: int | None = None
    num_comments: int | None = None
    top_comments: list[RedditComment] = Field(default_factory=list)
    sort: str = "best"


class GitHubRepoMetadata(BaseModel):
    """GitHub repo-specific metadata."""

    owner: str
    repo: str
    description: str | None = None
    language: str | None = None
    stars: int | None = None
    forks: int | None = None
    open_issues: int | None = None
    license: str | None = None
    homepage: str | None = None
    topics: list[str] = Field(default_factory=list)
    last_pushed_at: str | None = None


class Flashcard(BaseModel):
    """A single Q&A flashcard generated from saved content."""

    question: str
    answer: str


class RelatedNoteMatch(BaseModel):
    """A related existing note discovered in the user's vault."""

    title: str
    path: str
    score: float = Field(ge=0.0, le=1.0)
    shared_tags: list[str] = Field(default_factory=list)


class ExtractedContent(BaseModel):
    """Raw content extracted from a source, before AI processing."""

    source: CanonicalSource
    title: str
    text: str
    author: str | None = None
    site_name: str | None = None
    date_published: str | None = None
    word_count: int = 0
    source_metadata: RedditMetadata | GitHubRepoMetadata | None = None
    warnings: list[ExtractionWarning] = Field(default_factory=list)
    extraction_quality: float = Field(ge=0.0, le=1.0, default=1.0)


class AIEnrichment(BaseModel):
    """AI-generated enrichments for a piece of content."""

    summary: str
    key_ideas: list[str]
    key_quotes: list[str]
    counterarguments: list[str]
    tags: list[str]
    category: ArticleCategory = ArticleCategory.MISC
    rating: int = Field(ge=1, le=10)
    read_time_minutes: int = 0


class NoteFrontmatter(BaseModel):
    """YAML frontmatter for a vault note."""

    title: str
    source: str
    canonical_url: str
    type: SourceType
    author: str | None = None
    saved: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: list[str] = Field(default_factory=list)
    rating: int = Field(ge=1, le=10, default=5)
    read_time_minutes: int = 0
    status: NoteStatus = NoteStatus.PROCESSED
    content_hash: str = ""
    model_used: str = ""
    extraction_quality: float = Field(ge=0.0, le=1.0, default=1.0)
    vaultmind: bool = True
    # Reddit-specific
    subreddit: str | None = None
    # GitHub-specific
    repo_name: str | None = None
    language: str | None = None
    stars: int | None = None
    last_updated: str | None = None


class RenderedNote(BaseModel):
    """A fully rendered note ready to be written to the vault."""

    frontmatter: NoteFrontmatter
    body: str
    filename: str
    folder_path: str


# ---- Manifest models (for vm compile) ----


class ManifestSource(BaseModel):
    """A source note tracked in the manifest."""

    content_hash: str
    saved_at: datetime
    compiled_at: datetime | None = None
    wiki_articles: list[str] = Field(default_factory=list)


class ManifestWikiEntry(BaseModel):
    """A wiki article tracked in the manifest."""

    last_updated: datetime
    source_urls: list[str] = Field(default_factory=list)
    content_hash: str = ""


class Manifest(BaseModel):
    """Source of truth for the compile loop — tracks what has been compiled."""

    version: int = 1
    last_compiled: datetime | None = None
    sources: dict[str, ManifestSource] = Field(default_factory=dict)
    wiki_articles: dict[str, ManifestWikiEntry] = Field(default_factory=dict)


class ConceptStatus(StrEnum):
    NEW = "new"
    EXISTING = "existing"
    MERGE = "merge"


class WikiConceptEntry(BaseModel):
    """A concept extracted during concept triage."""

    name: str
    status: ConceptStatus
    description: str = ""
    source_urls: list[str] = Field(default_factory=list)
    merge_target: str | None = None
