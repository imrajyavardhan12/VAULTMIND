"""Tests for URL canonicalization."""

from vaultmind.utils.urls import canonicalize_url


def test_strip_utm_params():
    url = "https://example.com/article?utm_source=twitter&utm_medium=social&id=42"
    result = canonicalize_url(url)
    assert "utm_source" not in result
    assert "id=42" in result


def test_normalize_twitter_domain():
    url = "https://mobile.twitter.com/user/status/123"
    result = canonicalize_url(url)
    assert result.startswith("https://x.com/")


def test_normalize_old_reddit():
    url = "https://old.reddit.com/r/python/comments/abc/title/"
    result = canonicalize_url(url)
    assert "www.reddit.com" in result


def test_strip_trailing_slash():
    url = "https://example.com/article/"
    result = canonicalize_url(url)
    assert not result.endswith("/")


def test_strip_fragment():
    url = "https://example.com/article#section-1"
    result = canonicalize_url(url)
    assert "#" not in result


def test_strip_www():
    url = "https://www.example.com/article"
    result = canonicalize_url(url)
    assert "www." not in result
