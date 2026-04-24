"""Tests for Twitter/X extraction behavior."""

from __future__ import annotations

from vaultmind.core.twitter import extract_tweet
from vaultmind.schemas import CanonicalSource, SourceType


def _source(url: str) -> CanonicalSource:
    return CanonicalSource(
        original_url=url,
        canonical_url=url,
        source_type=SourceType.TWEET,
    )


async def test_extract_tweet_prefers_syndication(monkeypatch):
    async def fake_syndication(tweet_id: str):
        assert tweet_id == "123456789"
        return {
            "text": "This is the tweet body",
            "user": {"screen_name": "testuser"},
        }

    monkeypatch.setattr("vaultmind.core.twitter._fetch_syndicated_tweet", fake_syndication)
    monkeypatch.setattr("vaultmind.core.twitter.trafilatura.fetch_url", lambda url: None)

    content = await extract_tweet(_source("https://x.com/testuser/status/123456789"))
    assert content.text == "This is the tweet body"
    assert content.author == "@testuser"
    assert content.extraction_quality == 0.95


async def test_extract_tweet_rejects_javascript_gate_page(monkeypatch):
    async def fake_syndication(tweet_id: str):
        return None

    monkeypatch.setattr("vaultmind.core.twitter._fetch_syndicated_tweet", fake_syndication)
    monkeypatch.setattr("vaultmind.core.twitter.trafilatura.fetch_url", lambda url: "<html>x</html>")
    monkeypatch.setattr(
        "vaultmind.core.twitter.trafilatura.extract",
        lambda *args, **kwargs: (
            "We've detected that JavaScript is disabled in this browser. "
            "Please enable JavaScript or switch to a supported browser to continue using x.com. "
            "Some privacy related extensions may cause issues on x.com."
        ),
    )

    content = await extract_tweet(_source("https://x.com/testuser/status/111"))
    assert content.text == ""
    assert content.extraction_quality == 0.1
    assert any(w.code == "javascript_required" for w in content.warnings)


async def test_extract_tweet_fetch_failure_returns_empty(monkeypatch):
    async def fake_syndication(tweet_id: str):
        return None

    monkeypatch.setattr("vaultmind.core.twitter._fetch_syndicated_tweet", fake_syndication)
    monkeypatch.setattr("vaultmind.core.twitter.trafilatura.fetch_url", lambda url: None)

    content = await extract_tweet(_source("https://x.com/testuser/status/222"))
    assert content.text == ""
    assert content.extraction_quality == 0.1
    assert any(w.code == "fetch_failed" for w in content.warnings)
