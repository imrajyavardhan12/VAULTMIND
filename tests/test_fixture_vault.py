"""Tests for the fixture vault (Story #9).

These tests verify that the fixture vault is loadable, scannable,
and that using it does not mutate the source fixture files.
"""

from __future__ import annotations

from pathlib import Path

from vaultmind.core.manifest import read_manifest
from vaultmind.core.raw_scanner import scan_raw_sources
from vaultmind.schemas import Manifest


class TestFixtureVaultStructure:
    """Verify the fixture vault has the expected structure."""

    def test_fixture_vault_has_three_raw_sources(self, fixture_vault):
        """Scan returns exactly 3 raw source files."""
        records = scan_raw_sources(fixture_vault)
        assert len(records) == 3
        titles = {r.title for r in records}
        assert "Attention Mechanisms in Transformers" in titles
        assert "RLHF vs DPO: A Comparison of Alignment Methods" in titles
        assert "Sparse Attention Trade-offs in Transformer Models" in titles

    def test_raw_sources_have_frontmatter(self, fixture_vault):
        """Raw sources have source URLs in frontmatter."""
        records = scan_raw_sources(fixture_vault)
        for record in records:
            assert record.source_url is not None, f"Missing source_url for {record.title}"
            assert record.source_url.startswith("https://"), f"Invalid source_url for {record.title}"

    def test_raw_sources_have_body_content(self, fixture_vault):
        """Raw sources have meaningful body content."""
        records = scan_raw_sources(fixture_vault)
        for record in records:
            assert len(record.body) > 100, f"Body too short for {record.title}"
            assert record.content_hash, f"Missing content_hash for {record.title}"

    def test_fixture_vault_has_existing_wiki_concept(self, fixture_vault):
        """Wiki/Concepts contains the existing attention-mechanisms article."""
        concepts_dir = (
            fixture_vault.vault_path
            / fixture_vault.folders.wiki
            / fixture_vault.folders.wiki_concepts
        )
        assert concepts_dir.exists(), "Concepts directory does not exist"
        concept_files = list(concepts_dir.glob("*.md"))
        assert len(concept_files) == 1, f"Expected 1 concept, found {len(concept_files)}"
        assert concept_files[0].stem == "attention-mechanisms"

    def test_existing_concept_has_vaultmind_frontmatter(self, fixture_vault):
        """Existing concept has correct frontmatter."""
        concepts_dir = (
            fixture_vault.vault_path
            / fixture_vault.folders.wiki
            / fixture_vault.folders.wiki_concepts
        )
        concept_path = concepts_dir / "attention-mechanisms.md"
        text = concept_path.read_text(encoding="utf-8")
        assert text.startswith("---")
        assert "vaultmind: true" in text
        assert "kind: concept" in text
        assert "[[transformers]]" in text or "[[" in text


class TestFixtureVaultManifest:
    """Verify the fixture manifest has realistic state."""

    def test_manifest_loads_successfully(self, fixture_vault):
        """Manifest file is valid and loadable."""
        manifest = read_manifest(fixture_vault.vault_path)
        assert isinstance(manifest, Manifest)
        assert manifest.version == 1

    def test_manifest_has_one_compiled_source(self, fixture_vault):
        """Manifest tracks one source as already compiled."""
        manifest = read_manifest(fixture_vault.vault_path)
        assert len(manifest.sources) == 1
        source_url = "https://lena-voita.github.io/posts/annotated_transformers/attention.html"
        assert source_url in manifest.sources
        assert manifest.sources[source_url].wiki_articles == ["attention-mechanisms"]

    def test_manifest_content_hash_matches_real_hash(self, fixture_vault):
        """Manifest source hash matches actual content hash."""
        manifest = read_manifest(fixture_vault.vault_path)
        source_url = "https://lena-voita.github.io/posts/annotated_transformers/attention.html"
        record = next(r for r in scan_raw_sources(fixture_vault) if r.source_url == source_url)
        assert manifest.sources[source_url].content_hash == record.content_hash

    def test_manifest_has_one_wiki_article(self, fixture_vault):
        """Manifest tracks one wiki article."""
        manifest = read_manifest(fixture_vault.vault_path)
        assert len(manifest.wiki_articles) == 1
        assert "attention-mechanisms" in manifest.wiki_articles
        entry = manifest.wiki_articles["attention-mechanisms"]
        assert len(entry.source_urls) == 1
        assert entry.source_urls[0] == "https://lena-voita.github.io/posts/annotated_transformers/attention.html"


class TestFixtureVaultIsolation:
    """Verify that mutating the fixture vault does not affect the source."""

    def test_copy_is_independent(self, fixture_vault):
        """Mutating the copied vault does not modify source fixtures."""
        fixture_source = Path(__file__).parent / "fixtures" / "vault"

        # Get original file size
        original_file = fixture_source / "📥 Raw" / "attention-mechanisms-transformers.md"
        original_size = original_file.stat().st_size

        # Modify a file in the copied vault
        concepts_dir = (
            fixture_vault.vault_path
            / fixture_vault.folders.wiki
            / fixture_vault.folders.wiki_concepts
        )
        (concepts_dir / "attention-mechanisms.md").write_text(
            "# Modified\n\nThis should not affect source.",
            encoding="utf-8",
        )

        # Verify source fixture is unchanged
        source_size = original_file.stat().st_size
        assert source_size == original_size, "Source fixture was modified"
        original_text = original_file.read_text(encoding="utf-8")
        assert "This should not affect source." not in original_text
