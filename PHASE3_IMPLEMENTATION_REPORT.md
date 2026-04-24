# Phase 3 Implementation Report (PRD 3.1–3.9)

Date: 2026-03-30  
Project: VaultMind  
Scope: PRD Phase 3 detailed implementation spec (`3.1` to `3.9`)

## Executive Summary

Phase 3 is implemented end-to-end as specified in PRD sections `3.1–3.9`.
The code now supports:

1. Flashcard schema + generation pipeline
2. Related-note discovery via weighted Jaccard similarity
3. Wikilink injection using vault-relative path links
4. Post-render section appending for flashcards and related notes
5. Updated `vm save` execution order with Phase 3 steps
6. Test coverage for all new behaviors listed in PRD `3.9`

Validation result: `57 passed` via `uv run pytest -q`.

## 3.1 New Schema Models (`schemas.py`)

Implemented in:

- `src/vaultmind/schemas.py`

Added models:

1. `Flashcard`
   - `question: str`
   - `answer: str`
2. `RelatedNoteMatch`
   - `title: str`
   - `path: str` (vault-relative, no `.md`, POSIX style)
   - `score: float` with bounds `[0.0, 1.0]`
   - `shared_tags: list[str]`

## 3.2 Related Note Finder (`core/linker.py`)

Implemented in:

- `src/vaultmind/core/linker.py`

Implemented function:

- `find_related_notes(...) -> list[RelatedNoteMatch]`

Implemented algorithm and rules:

1. Weighted scoring:
   - `tag_score = jaccard(current_tags, candidate_tags)`
   - `title_score = jaccard(current_title_tokens, candidate_title_tokens)`
   - `total_score = 0.7 * tag_score + 0.3 * title_score`
2. Candidate filters:
   - only `vaultmind: true`
   - skip same `canonical_url`
   - require at least one shared tag or title token
   - skip score `< min_score`
3. Token normalization:
   - stopword filtering
   - lowercase normalization
   - regex tokenization `[a-z0-9]+`
4. Output:
   - sorted by `score desc`, `len(shared_tags) desc`, `title asc`
   - capped by `limit`
   - returns `[]` for empty/no-match cases
5. Reused `parse_frontmatter()` from `core/writer.py` per PRD.

## 3.3 Wikilink Injection

Implemented in:

- `src/vaultmind/core/renderers.py`
- `src/vaultmind/commands/save.py`

Implemented format:

- `[[vault-relative-path|Display Title]]`

Behavior:

1. Related note entries render as bullet list items in `## 🔗 Related Notes`
2. Optional shared tags are appended as inline code tags
3. Injection happens after base body render in `save.py`

## 3.4 Flashcard Generation

Implemented in:

- `src/vaultmind/ai/prompts.py`
- `src/vaultmind/ai/pipeline.py`
- `src/vaultmind/commands/save.py`

Implemented:

1. `FLASHCARD_PROMPT` template in `ai/prompts.py`
2. `build_flashcard_prompt(content, enrichment)` with:
   - title
   - summary
   - key ideas
   - content excerpt (first 6000 chars)
3. `generate_flashcards(content, enrichment, provider)` in `ai/pipeline.py`
4. Parsing behavior:
   - parses JSON payload `{"flashcards": [...]}`
   - validates question/answer strings
   - ignores malformed items
   - caps results at 5
5. Fail-open behavior:
   - on generation/parsing failure returns `[]` and does not break save
6. Control flag in `save.py`:
   - `config.ai.generate_flashcards and not no_flash`

## 3.5 Post-Render Section Injection (`core/renderers.py`)

Implemented in:

- `src/vaultmind/core/renderers.py`

Added helper:

- `append_note_sections(body, *, flashcards=None, related_notes=None) -> str`

Behavior:

1. Appends `## 🃏 Flashcards` when non-empty
2. Appends `## 🔗 Related Notes` when non-empty
3. Omits both sections entirely if empty
4. Preserves existing body and appends cleanly with spacing

## 3.6 Pipeline Order Update (`commands/save.py`)

Implemented in:

- `src/vaultmind/commands/save.py`

Pipeline now includes:

1. `generate_flashcards(...)` step (conditional)
2. `find_related_notes(...)` step
3. `append_note_sections(...)` step after `render_note_body(...)`

New imports added:

1. `generate_flashcards`
2. `find_related_notes`
3. `append_note_sections`

## 3.7 JSON Cleaning Refactor (`ai/pipeline.py`)

Implemented in:

- `src/vaultmind/ai/pipeline.py`

Refactor completed:

1. Extracted `_clean_json_response()`
2. Reused in:
   - `_parse_ai_response()`
   - `_parse_flashcard_response()`

Additional hardening:

1. Added `_safe_int()` for resilient numeric parsing in enrichment parsing

## 3.8 Files Modified

Per PRD list, implemented changes in:

1. `src/vaultmind/schemas.py`
2. `src/vaultmind/core/linker.py`
3. `src/vaultmind/ai/prompts.py`
4. `src/vaultmind/ai/pipeline.py`
5. `src/vaultmind/core/renderers.py`
6. `src/vaultmind/commands/save.py`

## 3.9 Tests Added/Updated

### New test file

1. `tests/test_linker.py`
   - empty vault returns `[]`
   - skips non-vaultmind notes
   - skips current note by canonical URL
   - higher score for more shared tags
   - title token overlap as secondary signal
   - result limit capping
   - vault-relative path format without `.md`
   - deterministic sorting

### Updated test files

1. `tests/test_prompts.py`
   - flashcard prompt includes title/summary/key ideas
2. `tests/test_pipeline.py`
   - valid flashcard JSON
   - fenced JSON parsing
   - invalid JSON returns `[]`
   - malformed items ignored
3. `tests/test_renderers.py`
   - appends flashcards
   - appends related notes
   - omits empty sections
   - validates `[[path|title]]` wikilink format

## Validation and Quality Checks

Executed:

1. `uv run pytest -q`

Result:

- `57 passed in 0.35s`

Note:

- `uv run ruff check src tests` could not run because `ruff` executable is not installed in current environment.

## Production-Readiness Notes

Implemented safeguards:

1. Fail-open flashcard generation to avoid save-command failure
2. Strict filtering for related-note candidates (`vaultmind`, canonical skip)
3. Deterministic sorting for stable outputs
4. Schema-level validation for score bounds and flashcard structures
5. Defensive parsing for malformed AI output and mixed-type payloads

Remaining non-Phase-3 considerations:

1. Add integration tests for full `save.py` flow with mocking of AI provider
2. Add lint/type-check CI gate (`ruff`, `mypy`) in environment with required binaries
3. Add performance guardrails for very large vault scans (if note count grows significantly)
