"""Tests for the compile pipeline internals."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from vaultmind.ai.compiler import _deduplicate_concepts, compile_sources
from vaultmind.core.raw_scanner import RawSourceRecord
from vaultmind.schemas import ConceptStatus, Manifest, WikiConceptEntry


class StubProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []
        self.model = "stub-model"

    async def complete(self, prompt: str, system: str = "") -> str:
        del system
        self.prompts.append(prompt)
        return self.responses.pop(0)


def _raw_source(*, slug: str, source_url: str | None = None) -> RawSourceRecord:
    return RawSourceRecord(
        path=Path(f"/tmp/{slug}.md"),
        relative_path=f"Clippings/{slug}",
        title=slug,
        source_url=source_url,
        body=f"# {slug}\n\nBody text from {slug}",
        content_hash=f"hash-{slug}",
        raw_tags=[],
    )


def test_compile_sources_updates_existing_article_with_relative_path_raw_body(test_config):
    source = _raw_source(slug="raw-a", source_url=None)
    article_dir = test_config.vault_path / test_config.folders.wiki / test_config.folders.wiki_concepts
    article_dir.mkdir(parents=True, exist_ok=True)
    (article_dir / "concept-a.md").write_text("# Concept A\n\nOld content", encoding="utf-8")

    triage = json.dumps(
        {
            "concepts": [
                {
                    "name": "Concept A",
                    "status": "existing:concept-a",
                    "description": "Existing concept",
                    "source_urls": [source.relative_path],
                    "merge_target": "concept-a",
                }
            ]
        }
    )
    provider = StubProvider([triage, "# Concept A\n\nUpdated content"])

    result, slug_to_urls = asyncio.run(
        compile_sources(
            [source],
            Manifest(),
            provider,
            test_config.vault_path,
            test_config.folders,
        )
    )

    assert result.articles_updated == 1
    assert result.articles_created == 0
    assert slug_to_urls == {"concept-a": [source.relative_path]}
    assert "Body text from raw-a" in provider.prompts[1]


def test_deduplicate_concepts_preserves_existing_status_when_response_omits_status():
    concepts = [
        WikiConceptEntry(
            name="Attention",
            status=ConceptStatus.EXISTING,
            description="Existing concept",
            source_urls=["https://example.com/a"],
            merge_target="attention",
        ),
        WikiConceptEntry(
            name="Self Attention",
            status=ConceptStatus.NEW,
            description="New overlap",
            source_urls=["https://example.com/b"],
        ),
    ]
    provider = StubProvider(
        [
            json.dumps(
                {
                    "concepts": [
                        {
                            "name": "Attention Mechanisms",
                            "description": "Merged concept",
                            "source_urls": ["https://example.com/a", "https://example.com/b"],
                        }
                    ]
                }
            )
        ]
    )

    deduped = asyncio.run(_deduplicate_concepts(concepts, provider))

    assert len(deduped) == 1
    assert deduped[0].status == ConceptStatus.EXISTING
    assert deduped[0].merge_target == "attention"
