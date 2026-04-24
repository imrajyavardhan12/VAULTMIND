# VaultMind Complete Project Guide

> Version target: current codebase as of 2026-03-30  
> Scope: end-to-end explanation of architecture, features, commands, and internal behavior

---

## 1) What VaultMind Is

VaultMind is a Python CLI that converts web content into structured Markdown knowledge notes inside your Obsidian vault.

At a high level:

1. You run `vm save <url>`.
2. VaultMind classifies the URL and extracts content.
3. AI enriches content into summary, key ideas, tags, counterarguments, rating.
4. VaultMind writes a durable `.md` note with frontmatter + sections.
5. It optionally appends flashcards and related-note wikilinks.
6. Phase 4 commands generate insights across your entire vault (`stats`, `find`, `brief`, `digest`, `reflect`, `flashcard`).

---

## 2) Core Design Principles

1. Local-first knowledge system: all outputs are local Markdown files in your vault.
2. Typed contracts: major pipeline objects are Pydantic models.
3. Provider abstraction: AI providers are behind a minimal protocol.
4. Fail-open behavior for non-critical AI tasks: if optional generation fails, save still succeeds.
5. Deterministic outputs where possible: scoring, sorting, path generation, frontmatter structure.

---

## 3) Project Structure (What Lives Where)

## CLI and entrypoint

- `src/vaultmind/main.py`
  - Defines Typer app.
  - Registers `save`, `version`, and phase-4 commands via `register_commands(app)`.

## Commands

- `src/vaultmind/commands/save.py` → URL ingestion and note creation
- `src/vaultmind/commands/stats.py` → vault health metrics dashboard
- `src/vaultmind/commands/find.py` → keyword/fuzzy search
- `src/vaultmind/commands/brief.py` → weekly synthesis (AI fast tier)
- `src/vaultmind/commands/digest.py` → topic synthesis + optional MOC generation (AI deep tier)
- `src/vaultmind/commands/reflect.py` → reflection report (AI deep tier)
- `src/vaultmind/commands/flashcard.py` → quiz mode from stored flashcards (no AI)

## Core content and vault logic

- `src/vaultmind/core/router.py` → source type detection
- `src/vaultmind/core/extractors.py` → extractor dispatcher
- `src/vaultmind/core/scraper.py` → article extraction (`trafilatura`)
- `src/vaultmind/core/reddit.py` → Reddit extraction + top comments
- `src/vaultmind/core/github.py` → GitHub metadata + README extraction
- `src/vaultmind/core/twitter.py` → best-effort Twitter/X scraping
- `src/vaultmind/core/renderers.py` → markdown body rendering + section appending
- `src/vaultmind/core/writer.py` → frontmatter render + atomic writes + dedup lookup
- `src/vaultmind/core/linker.py` → related-note matching

## Phase 4 shared foundation

- `src/vaultmind/core/vault_index.py`
  - Scans vault once and returns structured `VaultNoteRecord` objects.
- `src/vaultmind/core/search.py`
  - Search scoring and excerpt generation.
- `src/vaultmind/core/flashcards.py`
  - Flashcard extraction from saved notes.
- `src/vaultmind/core/moc.py`
  - MOC generation helpers and write path logic.

## AI layer

- `src/vaultmind/ai/providers/*` → provider implementations
- `src/vaultmind/ai/prompts.py` → all prompt templates
- `src/vaultmind/ai/pipeline.py` → save-time enrichment + flashcard generation
- `src/vaultmind/ai/json_utils.py` → shared JSON cleanup
- `src/vaultmind/ai/knowledge.py` → brief/digest/reflect generation models + logic

## Utilities

- `src/vaultmind/utils/urls.py` → canonicalization + source detection
- `src/vaultmind/utils/hashing.py` → content hash
- `src/vaultmind/utils/display.py` → Rich display helpers
- `src/vaultmind/utils/logging.py` → structlog setup

## Tests

- `tests/` contains unit and command-level tests.

---

## 4) Setup and Installation

## Requirements

1. Python 3.11+
2. Existing Obsidian vault path
3. At least one AI key (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`)

## Install

```bash
uv pip install -e .
```

This installs the `vm` command from:

- `pyproject.toml` → `[project.scripts] vm = "vaultmind.main:app"`

## Configure files

```bash
cp .env.example .env
cp config.example.yaml config.yaml
```

Then edit:

- `.env` for secrets
- `config.yaml` for vault path, provider chain, behavior flags

---

## 5) Configuration Deep Dive

## `.env` secrets

Typical fields:

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GITHUB_TOKEN` (optional for GitHub limits)
- `OLLAMA_BASE_URL` (for local Ollama mode)

## `config.yaml` key sections

## `vault_path`

Absolute root of your Obsidian vault.

## `folders`

Logical destination folders for notes and generated assets:

- inbox, articles, tools, threads, discussions, flashcards, digests, mocs, ideas, meta
- raw/wiki folders: `raw`, `wiki`, `wiki_concepts`, `wiki_queries`, `wiki_inbox`, `wiki_weekly`, `wiki_index`

## `ai`

- `default_provider`
- `fallback_chain`
- `max_tokens`
- feature flags (`generate_flashcards`, etc.)
- provider model map by tier (`fast`, `deep`)

## `preferences`

- default status and UX flags

## Effective precedence

Runtime behavior generally follows:

1. CLI options
2. Env vars
3. `config.yaml`
4. defaults

---

## 6) End-to-End Save Pipeline (`vm save`)

`vm save` is the ingestion backbone.

## Pipeline steps

1. Canonicalize and route URL (`route_url`)
2. Reject unsupported types
3. Duplicate lookup by canonical URL (`find_existing_note`)
4. Optional tag merge on duplicates
5. Extract source content (article/reddit/github/twitter)
6. Generate AI enrichment (`process_content`)
7. Compute content hash
8. Build note frontmatter
9. Optional flashcard generation (`generate_flashcards`)
10. Related-note discovery (`find_related_notes`)
11. Render source-specific body (`render_note_body`)
12. Append flashcards/related sections (`append_note_sections`)
13. Resolve folder route
14. Generate filename slug
15. Atomic write (`write_note`)

## `vm save` options

From CLI help:

- required argument: `url`
- `--tag`, `-t` (repeatable)
- `--folder`, `-f` (vault-relative override)
- `--force` (reprocess duplicate)
- `--no-flash` (skip flashcard generation)
- `--verbose`

## Duplicate behavior

1. Existing canonical URL + no `--force`
   - exits with warning
2. Existing canonical URL + extra tags
   - merges tags into existing note frontmatter
3. Existing canonical URL + `--force`
   - reprocesses and writes new output

---

## 7) Source-Specific Extraction Behavior

## Articles

- Extracted via `trafilatura`.
- Pulls cleaned text and metadata (title, author, sitename, date when available).

## Reddit

- Uses Reddit JSON endpoint (`.json`).
- Extracts post + top comments (up to 5).
- Uses retry with exponential backoff on 429/5xx.
- Captures warnings and degraded quality when needed.

## GitHub

- Parses owner/repo from URL.
- Fetches repo metadata from GitHub API.
- Fetches README raw text.
- Includes warnings when README is missing or fetch partially fails.

## Twitter/X

- Experimental, best-effort scrape via `trafilatura`.
- Returns warning metadata due no stable public API path.

---

## 8) AI Enrichment and Parsing

## Save-time enrichment (`ai/pipeline.py`)

Main responsibilities:

1. Truncate long content safely for prompt budget
2. Build source-specific prompt
3. Call provider (`provider.complete`)
4. Parse JSON into `AIEnrichment`
5. Guard/fallback if model returns invalid JSON

## Flashcard generation path

1. Build dedicated prompt from title + summary + key ideas + excerpt
2. Parse `{"flashcards": [{"question": "...", "answer": "..."}]}`
3. Ignore malformed items
4. Cap to 5 cards
5. Fail-open to `[]` on errors

## Shared JSON cleanup

`ai/json_utils.py` normalizes model outputs by stripping:

- markdown code fences
- optional leading `json` prefix

This utility is reused in pipeline and knowledge synthesis.

---

## 9) Note Structure and Vault Output

Each source note has:

1. YAML frontmatter:
   - title, source, canonical URL, type, author
   - saved timestamp
   - tags
   - rating, read time
   - status
   - content hash
   - model used
   - extraction quality
   - `vaultmind: true`
   - source-specific fields (subreddit/repo/stars/etc.)
2. Body sections:
   - summary
   - key ideas
   - key quotes
   - counterarguments
   - source notes
3. Appended sections (if available):
   - `## 🃏 Flashcards`
   - `## 🔗 Related Notes`

Related-note link format:

```markdown
[[vault-relative/path|Display Title]]
```

---

## 10) Related Notes (Phase 3 intelligence)

Related matching uses weighted Jaccard:

1. Tags overlap: 70% weight
2. Title token overlap: 30% weight

Candidate rules:

1. Only notes with `vaultmind: true`
2. Skip same `canonical_url`
3. Require shared tag or title token
4. Score must meet threshold

Sort order:

1. score descending
2. shared tags count descending
3. title ascending

---

## 11) Phase 4 Features (Knowledge Generation)

## 11.1 `vm stats`

Purpose:

- Show vault health and metadata quality without AI.

Computes:

1. total notes
2. vaultmind notes
3. notes this week
4. counts by type/status
5. top tags
6. average rating/read time
7. flashcard coverage percentage
8. tagless notes
9. partial/review notes
10. MOC candidates (tags with count >= 5)

Usage:

```bash
vm stats
vm stats --verbose
```

## 11.2 `vm find`

Purpose:

- Keyword/fuzzy search across indexed notes.

Search scoring model:

1. exact phrase in title: +60
2. exact phrase in tags: +40
3. exact phrase in body: +20
4. jaccard(query,title_tokens) * 30
5. jaccard(query,tag_tokens) * 25
6. fuzzy title ratio bonus if ratio >= 0.72
7. reject score < 15

Behavior:

1. Empty query returns most recent notes.
2. Non-empty query returns scored ranked matches with excerpts.

Usage:

```bash
vm find --query "agent memory"
vm find --query "attenton economi"   # typo-tolerant fuzzy title match
vm find                              # recent notes mode
```

## 11.3 `vm brief`

Purpose:

- Weekly summary over recent notes.

Pipeline:

1. scan vault notes
2. filter by days
3. trim by limit
4. call `generate_weekly_brief()` with fast-tier provider
5. render takeaway/themes/highlights/actionables

Usage:

```bash
vm brief
vm brief --days 30 --limit 40
```

## 11.4 `vm digest`

Purpose:

- Deep synthesis for one topic.

Pipeline:

1. scan notes
2. search matches by topic
3. choose top `limit`
4. call `generate_topic_digest()` with deep-tier provider
5. render synthesis
6. auto-generate MOC when threshold met unless disabled

MOC behavior:

1. default threshold: 5 matched notes
2. writes under configured MOC folder
3. includes frontmatter metadata and wikilinks

Usage:

```bash
vm digest "machine learning"
vm digest "ai agents" --limit 25
vm digest "local llm tooling" --no-moc
```

## 11.5 `vm reflect`

Purpose:

- Weekly mirror of themes, shifts, tensions, blindspots, questions, experiment.

Pipeline:

1. scan notes
2. filter by days
3. call `generate_reflection()` with deep-tier provider
4. render structured reflection panels/tables

Usage:

```bash
vm reflect
vm reflect --days 14 --limit 30
```

## 11.6 `vm flashcard`

Purpose:

- Quiz on existing saved flashcards only (no new AI call in this command).

Pipeline:

1. scan notes
2. optional topic filtering
3. parse flashcards from `## 🃏 Flashcards`
4. flatten, shuffle, apply limit
5. run session

Modes:

1. Interactive TTY mode:
   - space flip
   - n next
   - p previous
   - k known
   - u unsure
   - q quit
2. Non-TTY mode:
   - prints Q/A panels sequentially

Usage:

```bash
vm flashcard
vm flashcard --topic ai --limit 50
```

---

## 12) AI Knowledge Models (Phase 4)

Defined in `ai/knowledge.py`:

1. `WeeklyBrief`
2. `TopicDigest`
3. `ReflectionReport`
4. supporting models:
   - `BriefTheme`
   - `NoteReference`
   - `MocSection`

Generation functions:

1. `generate_weekly_brief(...)`
2. `generate_topic_digest(...)`
3. `generate_reflection(...)`

Fallback policy:

If model output fails parsing/validation, deterministic fallback reports are returned instead of hard failure.

---

## 13) Logging and Observability

Logging setup:

- `utils/logging.py`

Destinations:

1. Normal mode: JSON logs to `~/.local/share/vaultmind/vaultmind.log`
2. Verbose mode: console debug logs to stderr

User-facing output:

- Rich panels/tables/progress on stdout

---

## 14) Testing and Quality

Current test status:

- `88 passed`

Test coverage includes:

1. schemas, urls, router, renderers, writer, providers, pipeline
2. phase-3 linker/flashcards integration points
3. phase-4 foundation modules
4. phase-4 command behavior
5. AI knowledge parsing/fallback behavior

Run tests:

```bash
.venv/bin/pytest -q
```

Command registration smoke check:

```bash
PYTHONPATH=src .venv/bin/python -m vaultmind.main --help
```

---

## 15) Practical Usage Cookbook

## Save and enrich a URL

```bash
vm save https://example.com/article
```

## Save with manual tags

```bash
vm save https://example.com/article --tag ai --tag systems
```

## Force reprocess a previously saved canonical URL

```bash
vm save https://example.com/article --force
```

## Weekly status workflow

```bash
vm stats
vm brief --days 7
vm reflect --days 7
```

## Topic exploration workflow

```bash
vm find --query "agent memory"
vm digest "agent memory"
vm flashcard --topic "agent memory"
```

---

## 16) Error Cases and Troubleshooting

## No config found

Symptom:

- startup exits with config error

Fix:

```bash
cp config.example.yaml config.yaml
```

Then set a valid absolute `vault_path`.

## No provider available

Symptom:

- provider initialization exits with “No AI provider available”

Fix:

1. Set API key in `.env`
2. Ensure `config.yaml` provider exists in `ai.providers`
3. Ensure provider is present in fallback chain

## Extraction returns empty text

Possible causes:

1. paywall
2. blocked source
3. bad or inaccessible URL

Behavior:

- command exits gracefully and does not write an empty note

## Flashcards missing in quiz mode

Reason:

- `vm flashcard` does not generate new flashcards; it reads saved `## 🃏 Flashcards` sections only.

Fix:

1. Save notes without `--no-flash`
2. Verify source notes contain flashcard sections

---

## 17) Current Implementation Notes

1. `find`, `flashcard`, and `reflect` are implemented as command logic with rich/terminal interaction; full Textual app classes are not currently required for functional operation.
2. MOC generation is currently triggered by `vm digest` as an immediate side effect when threshold is met.
3. All outputs stay file-based in the vault; no database required.

---

## 18) Developer Workflow

## Typical dev loop

```bash
.venv/bin/pytest -q
PYTHONPATH=src .venv/bin/python -m vaultmind.main --help
```

## Add a new command safely

1. Implement command in `src/vaultmind/commands/<name>.py`
2. Register it in `commands/__init__.py`
3. Keep shared logic in `core/*` or `ai/*`, not inside command file
4. Add tests in `tests/test_commands/test_<name>.py`

## Add a new AI synthesis task

1. Add prompt template in `ai/prompts.py`
2. Add typed model in `ai/knowledge.py`
3. Add generator function with fallback behavior
4. Add parser tests for valid and invalid JSON

---

## 19) Feature Inventory Checklist

Implemented:

1. URL ingestion + extraction pipeline
2. AI enrichment for saved notes
3. folder routing and atomic writing
4. duplicate detection and tag merge behavior
5. related notes linking
6. inline flashcard generation and parsing
7. vault stats dashboard
8. vault search
9. weekly brief generation
10. topic digest generation
11. MOC generation from digest
12. weekly reflection generation
13. flashcard quiz mode from stored cards

---

## 20) Final Summary

VaultMind now supports full ingestion plus cross-note knowledge generation workflows:

1. Capture knowledge with `vm save`
2. Monitor vault health with `vm stats`
3. Retrieve information with `vm find`
4. Synthesize time-based and topic-based insight with `vm brief`, `vm digest`, `vm reflect`
5. Reinforce memory using `vm flashcard`

The system is modular, test-covered, local-first, and ready for continued extension.
