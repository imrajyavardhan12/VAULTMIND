"""Tests for AI pipeline."""

from vaultmind.ai.pipeline import _parse_ai_response, _parse_flashcard_response
from vaultmind.schemas import CanonicalSource, ExtractedContent, SourceType, ArticleCategory


def _make_content() -> ExtractedContent:
    return ExtractedContent(
        source=CanonicalSource(
            original_url="https://example.com",
            canonical_url="https://example.com",
            source_type=SourceType.ARTICLE,
        ),
        title="Test",
        text="Some text content",
        word_count=100,
    )


def test_parse_valid_json():
    response = '{"summary": "A summary", "key_ideas": ["idea1"], "key_quotes": ["quote1"], "counterarguments": ["counter1"], "tags": ["test"], "category": "Tech", "rating": 7, "read_time_minutes": 5}'
    result = _parse_ai_response(response, _make_content())
    assert result.summary == "A summary"
    assert result.rating == 7
    assert result.category == ArticleCategory.TECH


def test_parse_json_with_code_blocks():
    response = '```json\n{"summary": "A summary", "key_ideas": ["idea1"], "key_quotes": [], "counterarguments": [], "tags": ["test"], "category": "AI", "rating": 8, "read_time_minutes": 3}\n```'
    result = _parse_ai_response(response, _make_content())
    assert result.summary == "A summary"
    assert result.category == ArticleCategory.AI


def test_parse_invalid_json_fallback():
    response = "This is not JSON at all"
    result = _parse_ai_response(response, _make_content())
    assert "Failed to process" in result.summary
    assert result.category == ArticleCategory.MISC


def test_parse_invalid_category_fallback():
    response = '{"summary": "A summary", "key_ideas": ["idea1"], "key_quotes": [], "counterarguments": [], "tags": ["test"], "category": "InvalidCategory", "rating": 5, "read_time_minutes": 3}'
    result = _parse_ai_response(response, _make_content())
    assert result.category == ArticleCategory.MISC


def test_parse_flashcard_valid_json():
    response = '{"flashcards": [{"question": "Q1", "answer": "A1"}, {"question": "Q2", "answer": "A2"}]}'
    result = _parse_flashcard_response(response)
    assert len(result) == 2
    assert result[0].question == "Q1"
    assert result[0].answer == "A1"


def test_parse_flashcard_json_with_code_blocks():
    response = '```json\n{"flashcards": [{"question": "Q1", "answer": "A1"}]}\n```'
    result = _parse_flashcard_response(response)
    assert len(result) == 1
    assert result[0].question == "Q1"


def test_parse_flashcard_invalid_json_returns_empty():
    response = "Not JSON"
    result = _parse_flashcard_response(response)
    assert result == []


def test_parse_flashcard_ignores_malformed_items():
    response = '{"flashcards": [{"question": "Q1", "answer": "A1"}, {"question": "Q2"}, "bad", {"answer": "A3"}]}'
    result = _parse_flashcard_response(response)
    assert len(result) == 1
    assert result[0].question == "Q1"
