"""Tests for URL routing."""

from vaultmind.core.router import route_url
from vaultmind.schemas import SourceType


def test_route_article():
    source = route_url("https://example.com/blog/some-article")
    assert source.source_type == SourceType.ARTICLE
    assert source.canonical_url == "https://example.com/blog/some-article"


def test_route_github():
    source = route_url("https://github.com/owner/repo")
    assert source.source_type == SourceType.GITHUB


def test_route_reddit():
    source = route_url("https://old.reddit.com/r/python/comments/abc123/title/")
    assert source.source_type == SourceType.REDDIT
    assert "www.reddit.com" in source.canonical_url


def test_route_twitter():
    source = route_url("https://twitter.com/user/status/12345")
    assert source.source_type == SourceType.TWEET
    assert "x.com" in source.canonical_url


def test_route_youtube_unsupported():
    source = route_url("https://youtube.com/watch?v=abc123")
    assert source.source_type == SourceType.UNKNOWN
