"""Tests for prompt builders."""

from vaultmind.ai.prompts import build_flashcard_prompt, build_processing_prompt
from vaultmind.schemas import (
    AIEnrichment,
    ArticleCategory,
    CanonicalSource,
    ExtractedContent,
    GitHubRepoMetadata,
    RedditMetadata,
    SourceType,
)


def test_article_prompt():
    content = ExtractedContent(
        source=CanonicalSource(
            original_url="https://example.com",
            canonical_url="https://example.com",
            source_type=SourceType.ARTICLE,
        ),
        title="Test Article",
        text="Some content",
        author="Alice",
    )
    prompt = build_processing_prompt(content)
    assert "Test Article" in prompt
    assert "Alice" in prompt
    assert "Some content" in prompt


def test_reddit_prompt():
    content = ExtractedContent(
        source=CanonicalSource(
            original_url="https://reddit.com/r/python/comments/abc/test/",
            canonical_url="https://www.reddit.com/r/python/comments/abc/test",
            source_type=SourceType.REDDIT,
        ),
        title="Test Post",
        text="OP text\n\n--- TOP COMMENTS ---\n\nComment 1\nComment 2",
        author="user1",
        source_metadata=RedditMetadata(subreddit="python"),
    )
    prompt = build_processing_prompt(content)
    assert "r/python" in prompt
    assert "DISCUSSION" in prompt
    assert "OP text" in prompt
    assert "Comment 1" in prompt


def test_github_prompt():
    content = ExtractedContent(
        source=CanonicalSource(
            original_url="https://github.com/owner/repo",
            canonical_url="https://github.com/owner/repo",
            source_type=SourceType.GITHUB,
        ),
        title="owner/repo",
        text="# README\n\nSome content",
        source_metadata=GitHubRepoMetadata(
            owner="owner",
            repo="repo",
            language="Python",
            stars=1000,
            description="A cool tool",
        ),
    )
    prompt = build_processing_prompt(content)
    assert "owner/repo" in prompt
    assert "Python" in prompt
    assert "1000" in prompt
    assert "REPOSITORY" in prompt


def test_flashcard_prompt_contains_title_summary_and_key_ideas():
    content = ExtractedContent(
        source=CanonicalSource(
            original_url="https://example.com",
            canonical_url="https://example.com",
            source_type=SourceType.ARTICLE,
        ),
        title="Attention Economics",
        text="This is the content body.",
    )
    enrichment = AIEnrichment(
        summary="A concise summary.",
        key_ideas=["Idea one", "Idea two"],
        key_quotes=[],
        counterarguments=[],
        tags=["attention"],
        category=ArticleCategory.BUSINESS,
        rating=7,
    )

    prompt = build_flashcard_prompt(content, enrichment)
    assert "Attention Economics" in prompt
    assert "A concise summary." in prompt
    assert "Idea one" in prompt
    assert "Idea two" in prompt
