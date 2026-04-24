"""Tests for source-specific renderers and section appenders."""

from vaultmind.core.renderers import append_note_sections, render_note_body
from vaultmind.schemas import (
    AIEnrichment,
    ArticleCategory,
    CanonicalSource,
    ExtractedContent,
    Flashcard,
    GitHubRepoMetadata,
    RedditComment,
    RedditMetadata,
    RelatedNoteMatch,
    SourceType,
)


def _make_enrichment(**overrides) -> AIEnrichment:
    defaults = {
        "summary": "A test summary.",
        "key_ideas": ["Idea one", "Idea two"],
        "key_quotes": ["A verbatim quote."],
        "counterarguments": ["Counter one"],
        "tags": ["test"],
        "category": ArticleCategory.TECH,
        "rating": 7,
        "read_time_minutes": 5,
    }
    defaults.update(overrides)
    return AIEnrichment(**defaults)


def test_render_article_body():
    content = ExtractedContent(
        source=CanonicalSource(
            original_url="https://example.com",
            canonical_url="https://example.com",
            source_type=SourceType.ARTICLE,
        ),
        title="Test Article",
        text="Some text",
        author="Alice",
        site_name="Example Blog",
    )
    enrichment = _make_enrichment()
    body = render_note_body(content, enrichment)

    assert "# Test Article" in body
    assert "## 🧠 Summary" in body
    assert "A test summary." in body
    assert "Idea one" in body
    assert "A verbatim quote." in body
    assert "Counter one" in body
    assert "Author: Alice" in body
    assert "Publication: Example Blog" in body


def test_render_reddit_body():
    content = ExtractedContent(
        source=CanonicalSource(
            original_url="https://reddit.com/r/python/comments/abc/test/",
            canonical_url="https://www.reddit.com/r/python/comments/abc/test",
            source_type=SourceType.REDDIT,
        ),
        title="Test Reddit Post",
        text="OP text here",
        author="testuser",
        source_metadata=RedditMetadata(
            subreddit="python",
            post_author="testuser",
            score=42,
            num_comments=10,
            top_comments=[
                RedditComment(author="commenter1", body="Great insight!", score=15),
                RedditComment(author="commenter2", body="I disagree because...", score=8),
            ],
        ),
    )
    enrichment = _make_enrichment()
    body = render_note_body(content, enrichment)

    assert "# Test Reddit Post" in body
    assert "r/python" in body
    assert "u/testuser" in body
    assert "## 🧠 Discussion Summary" in body
    assert "## 💬 Top Comments" in body
    assert "u/commenter1" in body
    assert "Great insight!" in body


def test_render_github_body():
    content = ExtractedContent(
        source=CanonicalSource(
            original_url="https://github.com/owner/repo",
            canonical_url="https://github.com/owner/repo",
            source_type=SourceType.GITHUB,
        ),
        title="owner/repo",
        text="# Repo\n\nSome README content",
        source_metadata=GitHubRepoMetadata(
            owner="owner",
            repo="repo",
            description="A cool tool",
            language="Python",
            stars=1234,
            forks=56,
            license="MIT",
            last_pushed_at="2026-03-15T10:00:00Z",
            topics=["cli", "python", "automation"],
        ),
    )
    enrichment = _make_enrichment()
    body = render_note_body(content, enrichment)

    assert "# owner/repo" in body
    assert "## 🛠️ Tool Card" in body
    assert "Python" in body
    assert "1,234" in body  # formatted stars
    assert "MIT" in body
    assert "## ⚠️ Limitations" in body
    assert "`cli`" in body  # topics rendered as code


def test_append_note_sections_appends_flashcards():
    body = "# Test\n\n## 🧠 Summary\nSummary text."
    flashcards = [Flashcard(question="What is this?", answer="A test note.")]

    result = append_note_sections(body, flashcards=flashcards)

    assert "## 🃏 Flashcards" in result
    assert "**Q:** What is this?" in result
    assert "**A:** A test note." in result


def test_append_note_sections_appends_related_notes():
    body = "# Test\n\n## 🧠 Summary\nSummary text."
    related = [
        RelatedNoteMatch(
            title="The Attention Economy Is Broken",
            path="📚 Sources/AI/the-attention-economy-is-broken",
            score=0.8,
            shared_tags=["ai", "social-media"],
        )
    ]

    result = append_note_sections(body, related_notes=related)

    assert "## 🔗 Related Notes" in result
    assert "[[📚 Sources/AI/the-attention-economy-is-broken|The Attention Economy Is Broken]]" in result
    assert "`ai`" in result


def test_append_note_sections_omits_empty_sections():
    body = "# Test\n\n## 🧠 Summary\nSummary text."
    result = append_note_sections(body, flashcards=[], related_notes=[])
    assert result == body


def test_append_note_sections_uses_expected_wikilink_format():
    body = "# Test"
    related = [RelatedNoteMatch(title="Alpha", path="📚 Sources/AI/alpha", score=0.9, shared_tags=[])]

    result = append_note_sections(body, related_notes=related)

    assert "- [[📚 Sources/AI/alpha|Alpha]]" in result
