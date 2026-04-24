"""Tests for vm digest command."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from vaultmind.ai.knowledge import TopicDigest
from vaultmind.core.search import SearchMatch
from vaultmind.core.vault_index import VaultNoteRecord


def _match(slug: str, score: float = 80.0) -> SearchMatch:
    note = VaultNoteRecord(
        path=Path(f"/tmp/{slug}.md"),
        relative_path=f"📚 Sources/AI/{slug}",
        title=slug,
        saved_at=datetime.now(UTC),
        tags=["ai"],
        source_type="article",
        rating=8,
        read_time_minutes=4,
        status="processed",
        canonical_url=None,
        source=None,
        vaultmind=True,
        body="# body",
        summary="summary",
        raw_frontmatter={},
    )
    return SearchMatch(note=note, score=score, title_hits=[], tag_hits=[], excerpt="")


def _digest(topic: str) -> TopicDigest:
    return TopicDigest(
        topic=topic,
        thesis="thesis",
        patterns=[],
        tensions=[],
        standout_notes=[],
        open_questions=[],
        moc_sections=[],
    )


def test_digest_uses_deep_tier_and_writes_moc(monkeypatch, test_config):
    from vaultmind.commands import digest as digest_cmd

    called: dict[str, object] = {"wrote": False}
    matches = [_match(f"n{i}") for i in range(6)]

    monkeypatch.setattr(digest_cmd, "setup_logging", lambda verbose=False: None)
    monkeypatch.setattr(digest_cmd, "load_config", lambda: test_config)
    monkeypatch.setattr(digest_cmd, "scan_vault_notes", lambda config, only_vaultmind=True: [m.note for m in matches])
    monkeypatch.setattr(digest_cmd, "search_notes", lambda notes, topic, limit=50: matches)

    def fake_get_provider(config, tier="fast"):
        called["tier"] = tier
        return object()

    async def fake_generate(topic, selected, provider):
        called["selected"] = len(selected)
        return _digest(topic)

    monkeypatch.setattr(digest_cmd, "get_provider", fake_get_provider)
    monkeypatch.setattr(digest_cmd, "generate_topic_digest", fake_generate)
    monkeypatch.setattr(digest_cmd, "render_topic_digest", lambda report, selected: None)
    monkeypatch.setattr(digest_cmd, "should_generate_moc", lambda topic, selected: True)
    monkeypatch.setattr(
        digest_cmd,
        "write_moc",
        lambda topic, report, selected, config: called.__setitem__("wrote", True) or Path("/tmp/moc.md"),
    )
    monkeypatch.setattr(digest_cmd, "print_success", lambda title, message: None)

    digest_cmd.digest("ai", limit=5, no_moc=False, verbose=False)
    assert called["tier"] == "deep"
    assert called["selected"] == 5
    assert called["wrote"] is True


def test_digest_skips_moc_with_no_moc_flag(monkeypatch, test_config):
    from vaultmind.commands import digest as digest_cmd

    called = {"wrote": False}
    matches = [_match(f"n{i}") for i in range(6)]

    monkeypatch.setattr(digest_cmd, "setup_logging", lambda verbose=False: None)
    monkeypatch.setattr(digest_cmd, "load_config", lambda: test_config)
    monkeypatch.setattr(digest_cmd, "scan_vault_notes", lambda config, only_vaultmind=True: [m.note for m in matches])
    monkeypatch.setattr(digest_cmd, "search_notes", lambda notes, topic, limit=50: matches)
    monkeypatch.setattr(digest_cmd, "get_provider", lambda config, tier="deep": object())
    monkeypatch.setattr(digest_cmd, "render_topic_digest", lambda report, selected: None)
    monkeypatch.setattr(digest_cmd, "should_generate_moc", lambda topic, selected: True)
    monkeypatch.setattr(
        digest_cmd,
        "write_moc",
        lambda topic, report, selected, config: called.__setitem__("wrote", True),
    )

    async def fake_generate(topic, selected, provider):
        return _digest(topic)

    monkeypatch.setattr(digest_cmd, "generate_topic_digest", fake_generate)

    digest_cmd.digest("ai", limit=5, no_moc=True, verbose=False)
    assert called["wrote"] is False
