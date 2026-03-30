"""Tests for data models."""

from datetime import datetime, timezone

from vaultmind.schemas import (
    AIEnrichment,
    ArticleCategory,
    CanonicalSource,
    ExtractedContent,
    NoteFrontmatter,
    NoteStatus,
    RenderedNote,
    SourceType,
)


def test_canonical_source():
    source = CanonicalSource(
        original_url="https://example.com/article?utm_source=x",
        canonical_url="https://example.com/article",
        source_type=SourceType.ARTICLE,
    )
    assert source.source_type == SourceType.ARTICLE


def test_note_frontmatter_defaults():
    fm = NoteFrontmatter(
        title="Test",
        source="https://example.com",
        canonical_url="https://example.com",
        type=SourceType.ARTICLE,
    )
    assert fm.vaultmind is True
    assert fm.status == NoteStatus.PROCESSED
    assert fm.rating == 5
    assert isinstance(fm.saved, datetime)


def test_ai_enrichment_rating_bounds():
    enrichment = AIEnrichment(
        summary="test",
        key_ideas=["idea"],
        key_quotes=[],
        counterarguments=[],
        tags=["test"],
        category=ArticleCategory.TECH,
        rating=8,
    )
    assert enrichment.rating == 8


def test_reddit_metadata():
    from vaultmind.schemas import RedditComment, RedditMetadata
    meta = RedditMetadata(
        subreddit="python",
        post_author="user1",
        score=100,
        num_comments=50,
        top_comments=[
            RedditComment(author="c1", body="Great post!", score=20),
        ],
    )
    assert meta.subreddit == "python"
    assert len(meta.top_comments) == 1
    assert meta.top_comments[0].score == 20


def test_github_repo_metadata():
    from vaultmind.schemas import GitHubRepoMetadata
    meta = GitHubRepoMetadata(
        owner="octocat",
        repo="hello-world",
        language="Python",
        stars=5000,
        topics=["python", "cli"],
    )
    assert meta.owner == "octocat"
    assert meta.stars == 5000
    assert "cli" in meta.topics


def test_extraction_warning():
    from vaultmind.schemas import ExtractionWarning
    w = ExtractionWarning(code="rate_limited", message="Reddit returned 429")
    assert w.code == "rate_limited"


def test_extracted_content_with_metadata():
    from vaultmind.schemas import (
        CanonicalSource, ExtractedContent, RedditMetadata, SourceType
    )
    content = ExtractedContent(
        source=CanonicalSource(
            original_url="https://reddit.com/r/test/comments/abc/title/",
            canonical_url="https://www.reddit.com/r/test/comments/abc/title",
            source_type=SourceType.REDDIT,
        ),
        title="Test Post",
        text="Post body",
        source_metadata=RedditMetadata(subreddit="test"),
        extraction_quality=0.8,
    )
    assert content.extraction_quality == 0.8
    assert content.source_metadata.subreddit == "test"


def test_frontmatter_reddit_fields():
    from vaultmind.schemas import NoteFrontmatter, SourceType
    fm = NoteFrontmatter(
        title="Test",
        source="https://reddit.com/r/test",
        canonical_url="https://www.reddit.com/r/test",
        type=SourceType.REDDIT,
        subreddit="test",
    )
    assert fm.subreddit == "test"


def test_frontmatter_github_fields():
    from vaultmind.schemas import NoteFrontmatter, SourceType
    fm = NoteFrontmatter(
        title="Test",
        source="https://github.com/owner/repo",
        canonical_url="https://github.com/owner/repo",
        type=SourceType.GITHUB,
        repo_name="owner/repo",
        language="Python",
        stars=500,
        last_updated="2026-03-15",
    )
    assert fm.repo_name == "owner/repo"
    assert fm.stars == 500
