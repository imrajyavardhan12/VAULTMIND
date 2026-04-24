"""Tests for vault writer."""


from vaultmind.core.writer import generate_filename, resolve_folder, slugify, write_note
from vaultmind.schemas import (
    ArticleCategory,
    NoteFrontmatter,
    RenderedNote,
    SourceType,
)


def test_slugify():
    assert slugify("The Attention Economy Is Broken") == "the-attention-economy-is-broken"
    assert slugify("Hello! World? 🌍") == "hello-world"
    assert slugify("") == "untitled"


def test_slugify_max_length():
    long_title = "a" * 200
    slug = slugify(long_title)
    assert len(slug) <= 80


def test_generate_filename():
    filename = generate_filename("Test Article", "abc123")
    assert filename == "test-article.md"


def test_resolve_folder_article(test_config):
    folder = resolve_folder(SourceType.ARTICLE, ArticleCategory.AI, test_config)
    assert "📚 Sources" in str(folder)
    assert "AI" in str(folder)


def test_resolve_folder_reddit(test_config):
    folder = resolve_folder(SourceType.REDDIT, ArticleCategory.MISC, test_config)
    assert "💬 Discussions" in str(folder)


def test_resolve_folder_unknown(test_config):
    folder = resolve_folder(SourceType.UNKNOWN, ArticleCategory.MISC, test_config)
    assert "📥 Inbox" in str(folder)


def test_write_note(test_config):
    fm = NoteFrontmatter(
        title="Test Note",
        source="https://example.com",
        canonical_url="https://example.com",
        type=SourceType.ARTICLE,
        tags=["test"],
        content_hash="abc123",
    )
    note = RenderedNote(
        frontmatter=fm,
        body="# Test Note\n\nSome content.",
        filename="test-note.md",
        folder_path=str(test_config.vault_path / "📚 Sources" / "Misc"),
    )
    path = write_note(note, test_config)
    assert path.exists()
    content = path.read_text()
    assert "title: Test Note" in content
    assert "# Test Note" in content
    assert "vaultmind: true" in content
