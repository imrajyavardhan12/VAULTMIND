# VaultMind — Project Blueprint
> *Your personal AI-powered second brain. Feed it anything. Find everything.*

---

## Table of Contents

1. [What We're Building](#what-were-building)
2. [The Problem We're Solving](#the-problem-were-solving)
3. [System Architecture](#system-architecture)
4. [Feature List](#feature-list)
5. [Vault Structure](#vault-structure)
6. [Note Anatomy](#note-anatomy)
7. [CLI Commands](#cli-commands)
8. [Tech Stack](#tech-stack)
9. [Build Phases](#build-phases)
10. [Folder Structure (Code)](#folder-structure-code)
11. [Setup Requirements](#setup-requirements)
12. [Future Ideas](#future-ideas)

---

## What We're Building

**VaultMind** is a CLI tool that sits between the internet and your Obsidian vault.

You give it a URL — a tweet, Reddit post, GitHub repo, article, or YouTube video — and it:
1. Fetches and extracts the content
2. Processes it with AI (Claude, GPT, or local models)
3. Writes a beautifully structured Markdown note into your Obsidian vault
4. Links it to related notes you've already saved
5. Adds counterarguments, key quotes, and flashcards

The result: a vault that actually grows smarter the more you use it. Your bookmarks stop dying.

---

## The Problem We're Solving

You browse a lot. You save a lot. You revisit almost nothing.

| The Graveyard | The Reality |
|---|---|
| Twitter threads bookmarked | Never re-read |
| Reddit posts saved | Buried forever |
| GitHub repos starred | Can't remember what they do |
| Articles "read later" | Read never |
| Ideas you had | Lost in browser history |

VaultMind kills this cycle. Everything you save gets **processed, connected, and made findable.**

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                     YOU                             │
│            vm save <url>                            │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              URL ROUTER                             │
│  Detects: tweet / reddit / github / article / yt    │
└────┬──────────┬───────────┬───────────┬─────────────┘
     │          │           │           │
     ▼          ▼           ▼           ▼
  Twitter    Reddit      GitHub     Article
  Parser     JSON API    API        trafilatura
     │          │           │           │
     └──────────┴───────────┴───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              AI PIPELINE (LLM)                      │
│                                                     │
│  1. Summarize      → Core ideas in plain language   │
│  2. Extract        → Key quotes, data, links        │
│  3. Tag            → Topics, domains, type          │
│  4. Counterargue   → Steelman the opposite view     │
│  5. Rate           → Usefulness score (1–10)        │
│  ── Phase 3 additions ──────────────────────────── │
│  6. Link           → Find related notes in vault    │
│  7. Flashcards     → 3 Q&A pairs for learning       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│           OBSIDIAN VAULT WRITER                     │
│  Creates .md file in the right folder               │
│  Adds YAML frontmatter                              │
│  Inserts [[wikilinks]] to related notes             │
└─────────────────────────────────────────────────────┘
```

---

## Feature List

> **v1 Scope:**
> - ✅ Supported: Articles, GitHub repos, Reddit posts
> - ⚠️ Experimental: Twitter/X (fragile, no public API)
> - 🔮 Future: YouTube, newsletters, PDFs
> - 🔍 `vm find` uses keyword/fuzzy search in v1 (semantic search via ChromaDB planned for v2)

### Core Features (Phase 1 & 2)

| Feature | Description |
|---|---|
| `vm save <url>` | Process any URL and save to vault |
| Auto URL detection | Knows if it's a tweet, Reddit, GitHub, or article |
| AI summarization | Key ideas extracted cleanly |
| Auto-tagging | Topics assigned automatically |
| YAML frontmatter | Structured metadata on every note |
| Vault folder routing | Notes go to the right subfolder automatically |

### Smart Features (Phase 1–2)

| Feature | Description |
|---|---|
| Counterarguments | AI argues the other side of any idea |
| Key quotes | Extracts the most important lines verbatim |
| Source-specific parsing | Reddit gets top comments, GitHub gets repo purpose |

### Vault Intelligence (Phase 3)

| Feature | Description |
|---|---|
| Related note linking | Finds existing notes in your vault and links them |
| Inline flashcards | Auto-generated Q&A pairs stored in source note |

### Knowledge Generation (Phase 4)

| Feature | Description |
|---|---|
| `vm brief` | What did I save this week? Summary digest |
| `vm flashcard` | Quiz me on recent saves |
| `vm find "topic"` | Keyword/fuzzy search across all your notes (semantic search in v2) |
| `vm digest "AI"` | Monthly synthesis on a specific topic |
| `vm stats` | Vault health: total notes, top tags, streaks |
| `vm reflect` | Weekly thinking mirror — patterns, tensions, blind spots in your saves |

### Special Source Handling

#### Twitter / X
- Extracts full thread, not just first tweet
- Saves the core argument
- Notes notable replies or quote tweets
- Tags the author and thread topic

#### Reddit
- Extracts post + top 5 comments by `best` sort (real value is in comments)
- Summarizes the **discussion**, not just the OP
- Notes the subreddit as a tag
- Saves controversial/contrarian top comments separately
- **Operational:** User-Agent: `VaultMind/1.0`; retry with exponential backoff on 429/5xx; on failure, save post only with `status: partial`

#### GitHub Repos
- Reads README fully
- Answers: *What problem does this solve? Who is it for? How mature is it?*
- Saves as a **Tool Card** format (different from article notes)
- Tags: language, category (e.g. `dev-tool`, `AI`, `CLI`)
- Notes: install command, last updated, star count

#### Articles / Blog Posts
- Full content extraction (no ads, no nav, clean text)
- Author and publication noted
- Reading time estimated
- Key data points and statistics pulled out

#### YouTube (Future)
- Transcript extraction
- Chapter-by-chapter summary
- Key timestamps noted

---

## Vault Structure

```
/Users/rvs/Obsidian Vault/
│
├── 📥 Inbox/
│   └── (everything lands here if category is unclear)
│
├── 🗺️ MOCs/                          ← Maps of Content
│   ├── AI & Machine Learning.md
│   ├── Developer Tools.md
│   ├── Philosophy & Mental Models.md
│   └── (auto-generated as topics grow)
│
├── 📚 Sources/                        ← Processed saves
│   ├── AI/
│   ├── Tech/
│   ├── Philosophy/
│   ├── Business/
│   ├── Science/
│   ├── Design/
│   └── Misc/
│
├── 🛠️ Tools/                          ← GitHub repos
│   ├── CLI Tools/
│   ├── AI Tools/
│   ├── Dev Libraries/
│   └── Productivity/
│
├── 🐦 Threads/                        ← Twitter/X saves
│
├── 💬 Discussions/                    ← Reddit saves
│
├── 💡 Ideas/                          ← Your original thinking
│
├── 🃏 Flashcards/                     ← Future: spaced repetition (v1 stores inline)
│
├── 📊 Digests/                        ← Weekly/Monthly briefs
│   ├── Weekly/
│   └── Monthly/
│
└── ⚙️ Meta/
    ├── VaultMind Config.md
    └── Vault Stats.md
```

---

## Note Anatomy

Every note VaultMind creates follows this base structure. Source-specific variants (GitHub Tool Card, Reddit Discussion) extend this with additional fields:

```markdown
---
title: "The Attention Economy Is Broken"
source: https://example.com/article
canonical_url: https://example.com/article
type: article                          # article | tweet | reddit | github | video
author: "Nik Sharma"
saved: 2025-01-15T21:32:10Z           # ISO 8601 with timezone
tags: [attention, social-media, psychology, tech-criticism]
rating: 8                              # AI usefulness score 1–10
read_time_minutes: 12                  # Numeric for filtering/stats
status: processed                      # processed | partial | review | archived
content_hash: "a1b2c3d4"              # For duplicate detection
model_used: "claude-sonnet-4-20250514"       # Which model processed this
extraction_quality: 1.0                # 0.0–1.0, how clean was the extraction
vaultmind: true                        # Marks this as a VaultMind-generated note
---

# The Attention Economy Is Broken

## 🧠 Summary
3–5 sentence plain-language summary of the core idea.

## 💡 Key Ideas
- Most important point from the piece
- Second most important point
- Third point — with emphasis on what's actionable

## 📌 Key Quotes
> "The most memorable quote from the piece verbatim."

> "Second notable quote if there is one."

## ⚔️ Counterarguments
*What would a smart critic say about this?*
- The opposite view, steelmanned fairly
- A limitation or blind spot in the argument

## 🔗 Related Notes
- [[Social Media and Dopamine]]
- [[Deep Work - Cal Newport]]
- [[How Algorithms Shape Behaviour]]

## 🃏 Flashcards
> *Flashcards are stored inline in the source note for v1. The `vm flashcard` command reads them from here. Separate flashcard files will be added when spaced repetition is implemented.*

**Q:** What is the core claim this piece makes?
**A:** That social platforms are designed to exploit psychological vulnerabilities for engagement.

**Q:** What evidence is given?
**A:** Studies on variable reward schedules, internal documents from Meta.

**Q:** What's the strongest counterargument?
**A:** Users have agency; platforms provide genuine value and connection.

## 📎 Source Notes
*Reddit: Top comment by u/username argued that...*
*Thread context: Part of a broader debate about...*
```

---

## CLI Commands

```bash
# ── SAVE ──────────────────────────────────────────────
vm save <url>                    # Save any URL (auto-detects type)
vm save <url> --tag AI --tag tools  # Save with manual extra tags (repeatable)
vm save <url> --folder Ideas/    # Override auto-folder routing (vault-relative, validated)
vm save <url> --no-flash         # Skip flashcard generation

# ── REVIEW ────────────────────────────────────────────
vm brief                         # This week's saves, summarized
vm brief --days 30               # Last 30 days
vm digest "machine learning"     # Synthesis of a topic
vm stats                         # Vault health dashboard

# ── LEARN ─────────────────────────────────────────────
vm flashcard                     # Quiz on recent saves (random)
vm flashcard --tag "AI"          # Quiz on specific topic

# ── SEARCH ────────────────────────────────────────────
vm find "topic or question"      # Keyword/fuzzy search across vault (semantic in v2)

# ── REFLECT ───────────────────────────────────────────
vm reflect                       # Weekly mirror — what are you actually thinking about?

# ── MANAGE (Future) ───────────────────────────────────
# vm config                      # Edit settings (planned)
# vm list --recent               # List recently saved notes (planned)
# vm open <note-name>            # Open a note in Obsidian (planned)
```

> **Note on UI experience:**
> Commands like `vm save`, `vm brief`, `vm digest`, and `vm stats` use `rich` — they run, print beautiful output, and exit. Commands like `vm flashcard`, `vm find`, and `vm reflect` use `Textual` — they open an interactive interface you navigate with your keyboard.

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Language | Python 3.11+ | Main language |
| Package mgmt | `uv` + `pyproject.toml` | Fast, modern Python packaging with lockfile + hash pinning (PEP 621) |
| CLI framework | `typer` | Clean commands with help text |
| Terminal output | `rich` | Beautiful output, progress bars, panels — for fire-and-done commands |
| Interactive UI | `Textual` | Full TUI for interactive commands (flashcards, find, reflect) |
| Article scraping | `trafilatura` | Extracts clean text from any article |
| HTTP client | `httpx` | Async HTTP for all API calls and scraping |
| Reddit | Reddit JSON API | No auth needed, free |
| GitHub | GitHub REST API | README + repo metadata |
| Twitter | URL-based extraction | Thread parsing |
| AI | Custom provider abstraction | Thin `Provider` protocol supporting Anthropic, OpenAI, Ollama/LM Studio |
| AI SDKs | `anthropic`, `openai` | Official SDKs — only what we need, no bloated wrappers |
| Config | `pydantic-settings` + `.env` | Typed, validated config with env var support; secrets stay in `.env` |
| Retry/resilience | `tenacity` | Retry logic for flaky AI/network calls with exponential backoff |
| Logging | `structlog` | Structured JSON logging for debugging pipelines |
| Note writing | Python `pathlib` | Creates and writes `.md` files |
| Testing | `pytest` + `pytest-asyncio` | Full test coverage with async support |
| Linting | `ruff` | Fastest Python linter + formatter (replaces black/isort/flake8) |
| Type checking | `mypy` | Static type checking — catch bugs before runtime |
| Search (future) | `chromadb` | Local vector database for semantic search |

**Both `rich` and `Textual` are from the same creator (Will McGugan) and actively maintained — latest versions as of early 2026.**

**No database. No Docker. No cloud. Everything is local files.**

### Config Ownership & Precedence

| Source | What It Stores | Read at Runtime? |
|---|---|---|
| `.env` | API keys, secrets only | Yes — via `pydantic-settings` |
| `config.yaml` | Vault path, folders, AI settings, preferences | Yes — loaded at startup |
| CLI flags | Per-run overrides (`--tag`, `--folder`, `--provider`) | Yes — highest priority |
| `⚙️ Meta/VaultMind Config.md` | Generated status/docs for the vault | **No** — display only |

**Precedence:** `CLI flags` > `ENV vars` > `config.yaml` > `defaults`

`config.yaml` location: project root (next to `pyproject.toml`), or `~/.config/vaultmind/config.yaml`.

### Async Boundary

- **Typer commands are sync.** They call async services via `asyncio.run()`.
- **Textual apps own their event loop** and call shared async services directly.
- **All HTTP calls (httpx) and AI provider calls are async internally.**
- This means the pipeline code is async-first; only the CLI entry points are sync wrappers.

### Logging & Output Policy

| Channel | Destination | Format |
|---|---|---|
| User-facing output | **stdout** via Rich/Textual | Pretty-printed panels, progress bars |
| Structured logs | **`~/.local/share/vaultmind/vaultmind.log`** | JSON via structlog |
| Debug mode (`--verbose`) | **stderr** | Human-readable structlog |

Structlog never writes to stdout during normal operation — it would corrupt Rich/Textual UI.

### Why No LiteLLM?

We use a custom ~100-line `Provider` protocol instead of LiteLLM. Reasons:
1. **Minimal attack surface** — LiteLLM was hit by a supply chain attack (March 2026). Fewer dependencies = fewer risks.
2. **We only need 3 providers** — Anthropic, OpenAI, Ollama. LiteLLM supports 100+. We don't need that complexity.
3. **Full control** — our abstraction is simple, typed, and debuggable. No magic, no hidden behavior.

### Multi-Model Strategy

Not all tasks need the same model. VaultMind uses a tiered approach:

```yaml
ai:
  default_provider: "anthropic"         # anthropic | openai | ollama
  fallback_chain: ["anthropic", "openai", "ollama"]
  providers:
    anthropic:
      models:
        fast: "claude-sonnet-4-20250514"
        deep: "claude-opus-4-5"
    openai:
      models:
        fast: "gpt-4.1-mini"
        deep: "gpt-4.1"
    ollama:
      base_url: "http://localhost:11434"
      models:
        fast: "llama3"
        deep: "llama3"
```

| Task | Model Tier | Why |
|---|---|---|
| `vm save` (summarize, tag) | `fast` | High volume, needs speed not depth |
| `vm save` (counterargue) | `fast` | Standard reasoning is sufficient |
| `vm reflect` | `deep` | Needs nuanced pattern recognition |
| `vm digest` | `deep` | Cross-note synthesis requires depth |
| `vm brief` | `fast` | Summarization of summaries |
| `vm flashcard` generation | `fast` | Simple Q&A extraction |
| Offline/free mode | `local` | No API costs, works without internet |

### Which commands use which UI tool

| Command | UI Tool | Why |
|---|---|---|
| `vm save <url>` | `rich` | Fire-and-done — watch it process, see the result |
| `vm brief` | `rich` | Read-only output, just needs to look good |
| `vm digest` | `rich` | Long-form output, no interaction needed |
| `vm stats` | `rich` | Dashboard display |
| `vm flashcard` | `Textual` | Interactive — flip cards, answer, navigate |
| `vm find` | `Textual` | Scroll results, open notes interactively |
| `vm reflect` | `Textual` | Read insights, navigate between them |

---

### Folder Routing Rules

Routing follows **source-type-first** logic:

| Source Type | Primary Folder | Subfolder Logic |
|---|---|---|
| Article/Blog | `📚 Sources/` | AI picks from fixed enum: `AI/`, `Tech/`, `Philosophy/`, `Business/`, `Science/`, `Design/`, `Misc/`. Falls back to `Misc/` |
| GitHub repo | `🛠️ Tools/` | AI picks from fixed enum: `CLI Tools/`, `AI Tools/`, `Dev Libraries/`, `Productivity/` |
| Reddit post | `💬 Discussions/` | Flat (no subfolders) |
| Twitter/X | `🐦 Threads/` | Flat (no subfolders) |
| Unknown/unclear | `📥 Inbox/` | Always — user triages manually |

**Precedence:** `--folder` CLI flag > source-type routing > Inbox fallback

**`--folder` validation:** must resolve under vault root. Paths like `../../Desktop` are rejected.

### Filename Strategy

Notes use a deterministic, filesystem-safe naming scheme:

| Rule | Example |
|---|---|
| Base | Slugified title: `the-attention-economy-is-broken.md` |
| Slugification | Lowercase, hyphens for spaces, strip punctuation/emoji, max 80 chars |
| Collision | Append short content hash: `the-attention-economy-is-broken--a1b2c3d4.md` |
| Frontmatter title | Stays human-readable: `"The Attention Economy Is Broken"` |
| Wikilinks | Use `[[filename\|Display Title]]` when filename differs from title |

Unicode is NFC-normalized to avoid macOS vs Linux inconsistencies.

### Duplicate Handling

When `vm save` detects a duplicate (by canonical URL or content hash):

| Scenario | Behavior |
|---|---|
| Exact duplicate (same URL) | Skip processing. Print existing note path. Exit 0. |
| Same URL + new `--tag` flags | Merge new tags into existing note frontmatter. Skip reprocessing. |
| `vm save <url> --force` | Re-fetch, re-process, overwrite existing note. |
| Different URL, same content hash | Warn user, save as new note (different source = different note). |

---

## Build Phases

### ✅ Phase 1 — Core Pipeline (Week 1)
> *Goal: `vm save <url>` works end-to-end for articles*

- [ ] Project setup (`uv`, `pyproject.toml`, config, `.env`)
- [ ] Typed data models (`schemas.py` — pipeline contracts)
- [ ] URL canonicalization (strip tracking params, normalize domains)
- [ ] Duplicate detection (by canonical URL + content hash)
- [ ] `trafilatura` article extraction
- [ ] AI provider abstraction + Anthropic/OpenAI/Ollama providers
- [ ] AI pipeline — summarize, tag, counterargue, rate
- [ ] YAML frontmatter generation (full schema)
- [ ] Atomic `.md` file write to Obsidian vault
- [ ] Basic folder routing (source-type-first, then topic)

**Done when:** You paste an article URL and a note appears in your vault.

---

### ✅ Phase 2 — CLI + Source Types (Week 2)
> *Goal: Full CLI, Reddit and GitHub support*

- [ ] `typer` CLI with all `vm save` options
- [ ] `rich` terminal output (progress, success messages)
- [ ] Reddit URL parser + top comment extraction
- [ ] GitHub URL parser + README extraction + repo metadata
- [ ] Source-specific note templates (GitHub Tool Card, Reddit Discussion)
- [ ] Twitter URL basic extraction (experimental)
- [ ] Error handling (paywalls, dead links, rate limits)

**Done when:** `vm save <reddit-url>` and `vm save <github-url>` both work.

---

### ✅ Phase 3 — Vault Intelligence (Week 3)
> *Goal: Notes link to each other, vault becomes a graph*

- [ ] Related note finder (scans existing vault, matches by tags + content)
- [ ] `[[wikilink]]` injection into new notes
- [ ] Inline flashcard generation (stored in source note, separate AI prompt)
- [x] ~~Note rating system~~ — already implemented in Phase 1 (AI scores 1–10 in every save)

**Done when:** New notes automatically reference old ones. Graph view has real connections.

#### Phase 3 — Detailed Implementation Spec

##### 3.1 New Schema Models (`schemas.py`)

Add two new models:

```python
class Flashcard(BaseModel):
    question: str
    answer: str

class RelatedNoteMatch(BaseModel):
    title: str
    path: str              # vault-relative path without .md, posix style
    score: float = Field(ge=0.0, le=1.0)
    shared_tags: list[str] = Field(default_factory=list)
```

##### 3.2 Related Note Finder (`core/linker.py`)

**Function signature:**
```python
def find_related_notes(
    *,
    current_title: str,
    current_tags: list[str],
    current_canonical_url: str,
    config: AppConfig,
    limit: int = 5,
    min_score: float = 0.15,
) -> list[RelatedNoteMatch]:
```

**Algorithm — weighted Jaccard similarity:**
- `tag_score = jaccard(current_tags, candidate_tags)` — 70% weight
- `title_score = jaccard(current_title_tokens, candidate_title_tokens)` — 30% weight
- `total_score = (0.7 * tag_score) + (0.3 * title_score)`

**Jaccard formula:**
```python
def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)
```

**Candidate filtering rules:**
- Only notes where `vaultmind: true` in frontmatter
- Skip notes where `canonical_url == current_canonical_url`
- Skip notes where `total_score < min_score`
- Require at least 1 shared tag OR 1 shared title token

**Tokenization:**
```python
STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
             "how", "in", "is", "it", "of", "on", "or", "that", "the", "to",
             "what", "when", "why", "with"}

def _normalize_tags(tags) -> set[str]:
    # handle None, non-list, strip/lowercase each tag

def _tokenize_title(title: str) -> set[str]:
    # regex [a-z0-9]+, filter stopwords, min length 2
```

**Return format:**
- Sort by `score` desc, `len(shared_tags)` desc, `title` asc
- Return top `limit` results
- Return `[]` if vault is empty or no matches

**Key detail:** Reuse `parse_frontmatter()` from `core/writer.py`.

##### 3.3 Wikilink Injection

**Format:** `[[vault-relative-path|Display Title]]` — NOT `[[Title]]`

Reason: filenames are slugified and may include `--hash` suffixes, so title ≠ filename.

**Example output:**
```markdown
## 🔗 Related Notes
- [[📚 Sources/AI/the-attention-economy-is-broken|The Attention Economy Is Broken]] — `ai`, `social-media`
- [[🛠️ Tools/astral-shuv|astral-sh/uv]] — `python`
```

**Where:** Call linker in `save.py` after enrichment, inject into body after rendering.

##### 3.4 Flashcard Generation

**Separate AI prompt — NOT part of main enrichment JSON.**

**New prompt (`ai/prompts.py`):**
```python
FLASHCARD_PROMPT = """Create 3-5 flashcards from the note below.
Return ONLY valid JSON: {"flashcards": [{"question": "...", "answer": "..."}]}
...
Title: {title}
Summary: {summary}
Key Ideas: {key_ideas}
Content Excerpt: {content}
"""

def build_flashcard_prompt(content, enrichment) -> str:
    # Use first 6000 chars of content + enrichment summary/ideas
```

**New pipeline function (`ai/pipeline.py`):**
```python
async def generate_flashcards(
    content: ExtractedContent,
    enrichment: AIEnrichment,
    provider: Provider,
) -> list[Flashcard]:
```

- Parse JSON response → `list[Flashcard]`
- On failure: log warning, return `[]` (fail-open, never break save)
- Cap at 5 flashcards max

**Control flag:**
```python
should_generate = config.ai.generate_flashcards and not no_flash
flashcards = await generate_flashcards(...) if should_generate else []
```

**Injection format:**
```markdown
## 🃏 Flashcards
**Q:** What problem does this solve?
**A:** It solves...

**Q:** Why is X important?
**A:** Because...
```

##### 3.5 Post-Render Section Injection (`core/renderers.py`)

Add a new helper (do NOT modify existing `render_note_body()`):

```python
def append_note_sections(
    body: str,
    *,
    flashcards: list[Flashcard] | None = None,
    related_notes: list[RelatedNoteMatch] | None = None,
) -> str:
```

- Appends `## 🃏 Flashcards` section if flashcards is non-empty
- Appends `## 🔗 Related Notes` section if related_notes is non-empty
- Omits sections entirely if lists are empty

##### 3.6 Pipeline Order (`commands/save.py`)

Updated pipeline (new steps marked with ★):

```
1.  route_url(url)
2.  find_existing_note(...)
3.  extract_source(...)
4.  process_content(...) → AIEnrichment
5.  content_hash(...)
6.  merge tags (enrichment.tags + CLI --tag)
7.  build frontmatter
8.  ★ generate_flashcards(...) if enabled, else []
9.  ★ find_related_notes(title, all_tags, canonical_url, config)
10. render_note_body(content, enrichment)
11. ★ append_note_sections(body, flashcards, related_notes)
12. resolve folder + generate filename
13. write_note(...)
```

**New imports in `save.py`:**
```python
from vaultmind.ai.pipeline import generate_flashcards, process_content
from vaultmind.core.linker import find_related_notes
from vaultmind.core.renderers import append_note_sections, render_note_body
```

##### 3.7 Refactor: Extract `_clean_json_response()` in `pipeline.py`

The JSON fence-stripping logic in `_parse_ai_response()` should be extracted into a shared helper `_clean_json_response()` and reused by both `_parse_ai_response()` and `_parse_flashcard_response()`.

##### 3.8 Files to Modify

| File | Change |
|---|---|
| `schemas.py` | Add `Flashcard`, `RelatedNoteMatch` |
| `core/linker.py` | Implement `find_related_notes()` + helpers |
| `ai/prompts.py` | Add `FLASHCARD_PROMPT`, `build_flashcard_prompt()` |
| `ai/pipeline.py` | Add `generate_flashcards()`, `_parse_flashcard_response()`, extract `_clean_json_response()` |
| `core/renderers.py` | Add `append_note_sections()` |
| `commands/save.py` | Wire flashcards + linker + append_note_sections into pipeline |

##### 3.9 Tests to Write

| Test File | Test Cases |
|---|---|
| `tests/test_linker.py` (new) | empty vault returns `[]`; skips non-vaultmind notes; skips current note; scores higher for more shared tags; title tokens as secondary; caps at limit; returns vault-relative paths; sorts by score desc |
| `tests/test_prompts.py` | flashcard prompt contains title/summary/key_ideas |
| `tests/test_pipeline.py` | parse valid flashcard JSON; parse with code fences; invalid JSON returns `[]`; ignores malformed items |
| `tests/test_renderers.py` | `append_note_sections()` — appends flashcards; appends related notes; omits empty sections; wikilink format is `[[path\|title]]` |

---

### ✅ Phase 4 — Knowledge Generation (Week 4)
> *Goal: Vault generates insights, not just stores them*

- [ ] `vm brief` — weekly digest of saves
- [ ] `vm digest "topic"` — synthesis of a topic across all notes
- [ ] `vm find "topic"` — keyword/fuzzy search across vault (Textual)
- [ ] `vm flashcard` — interactive quiz mode (Textual)
- [ ] `vm stats` — vault health dashboard
- [ ] `vm reflect` — weekly thinking mirror (Textual): surfaces patterns, tensions, blind spots
- [ ] MOC (Map of Content) auto-generation for growing topics

**Done when:** You run `vm reflect` on Sunday and it tells you something true about what you've been thinking about all week.

#### Phase 4 — Detailed Implementation Spec

##### 4.0 Implementation Order

Build in this order — each step unlocks the next:

```
1. Shared foundation (vault_index, search, flashcards, json_utils)
2. vm stats          ← pure scan, no AI, validates index
3. vm find           ← validates search + Textual plumbing
4. vm brief          ← first AI synthesis, lowest-risk prompt
5. vm digest         ← reuses search + AI, highest leverage
6. MOC generation    ← small add-on once digest exists
7. vm reflect        ← reuses weekly scan + AI, wraps in TUI
8. vm flashcard      ← stored-card quiz, no extra AI call needed
```

##### 4.1 Shared Foundation — New Modules

**Before building any command, create these shared modules:**

###### `core/vault_index.py` — Vault scanning layer

All commands reuse this instead of duplicating `rglob` + `parse_frontmatter` logic.

```python
@dataclass(slots=True)
class VaultNoteRecord:
    path: Path
    relative_path: str          # vault-relative, no .md, posix
    title: str
    saved_at: datetime | None
    tags: list[str]
    source_type: str | None
    rating: int | None
    read_time_minutes: int | None
    status: str | None
    canonical_url: str | None
    source: str | None
    vaultmind: bool
    body: str                   # markdown body without frontmatter
    summary: str                # extracted from ## 🧠 Summary section
    raw_frontmatter: dict[str, Any]

def scan_vault_notes(config: AppConfig, *, only_vaultmind: bool = True) -> list[VaultNoteRecord]
def filter_notes_by_days(notes, *, days: int, now: datetime | None = None) -> list[VaultNoteRecord]
def parse_saved_at(value: object) -> datetime | None
def read_markdown_body(path: Path) -> str
def extract_summary_from_body(body: str) -> str
def truncate_for_ai(text: str, *, max_chars: int = 1200) -> str
def format_note_packet(note: VaultNoteRecord, *, max_chars: int = 1200) -> str
```

**`extract_summary_from_body()` heuristic:** regex for `## 🧠 Summary`, `## 🧠 Discussion Summary`, `## Summary`, or first paragraph after `# Title`. Capture until next `##`.

**`format_note_packet()`:** compact format for AI prompts:
```
Title: {title}
Path: {relative_path}
Saved: {saved_at}
Tags: {tags}
Rating: {rating}
Summary: {summary}
```

###### `core/search.py` — Keyword/fuzzy search

Used by `vm find`, `vm digest`, `vm flashcard --topic`, and MOC candidate selection.

```python
@dataclass(slots=True)
class SearchMatch:
    note: VaultNoteRecord
    score: float
    title_hits: list[str]
    tag_hits: list[str]
    excerpt: str

def search_notes(notes, query: str, *, limit: int = 50) -> list[SearchMatch]
def score_note_match(note: VaultNoteRecord, query: str) -> SearchMatch | None
def build_match_excerpt(body: str, query: str, *, radius: int = 160) -> str
```

**Scoring formula (additive):**
- exact query phrase in title: `+60`
- exact query phrase in tags: `+40`
- exact query phrase in body: `+20`
- `jaccard(query_tokens, title_tokens) * 30`
- `jaccard(query_tokens, tag_set) * 25`
- fuzzy title ratio (`SequenceMatcher`) if `>= 0.72`: `+ ratio * 20`
- reject if score `< 15`

Reuse `_jaccard`, `_normalize_tags`, `_tokenize_title` from `core/linker.py`.

###### `core/flashcards.py` — Flashcard extraction from saved notes

```python
@dataclass(slots=True)
class NoteFlashcardDeck:
    note: VaultNoteRecord
    cards: list[Flashcard]

def extract_flashcards_from_body(body: str) -> list[Flashcard]
def collect_flashcard_decks(notes: Sequence[VaultNoteRecord]) -> list[NoteFlashcardDeck]
```

Parse `## 🃏 Flashcards` section line-by-line: `**Q:**` / `**A:**` pairs until next `##`.

###### `core/moc.py` — MOC helpers

```python
AUTO_MOC_MIN_NOTES = 5

def get_moc_path(topic: str, config: AppConfig) -> Path
def should_generate_moc(topic: str, matches, *, min_notes: int = 5) -> bool
def render_moc_markdown(topic: str, digest: TopicDigest, matches) -> str
def write_moc(topic: str, digest: TopicDigest, matches, config: AppConfig) -> Path
```

MOC is auto-generated as a **side-effect of `vm digest`** when `len(matches) >= 5`. No background job.

###### `ai/json_utils.py` — Shared JSON cleanup

Extract `_clean_json_response()` from `ai/pipeline.py` into:

```python
def clean_json_response(response: str) -> str
```

Reuse in `pipeline.py` and `ai/knowledge.py`.

###### `ai/knowledge.py` — AI synthesis layer

All AI-powered generation for brief/digest/reflect lives here.

```python
class WeeklyBrief(BaseModel):
    period_label: str
    one_sentence_takeaway: str
    themes: list[BriefTheme]
    highlights: list[NoteReference]
    gaps: list[str]
    suggested_next_steps: list[str]

class TopicDigest(BaseModel):
    topic: str
    thesis: str
    patterns: list[str]
    tensions: list[str]
    standout_notes: list[NoteReference]
    open_questions: list[str]
    moc_sections: list[MocSection]

class ReflectionReport(BaseModel):
    period_label: str
    dominant_themes: list[str]
    belief_shifts: list[str]
    tensions: list[str]
    blindspots: list[str]
    questions_for_you: list[str]
    recommended_experiment: str

async def generate_weekly_brief(notes, provider, *, period_label) -> WeeklyBrief
async def generate_topic_digest(topic, matches, provider) -> TopicDigest
async def generate_reflection(notes, provider, *, period_label) -> ReflectionReport
```

###### `ai/prompts.py` — New prompts

Add:
- `KNOWLEDGE_SYSTEM_PROMPT` — grounding rules for synthesis
- `WEEKLY_BRIEF_PROMPT` — uses `{period_label}` + `{notes_payload}`
- `TOPIC_DIGEST_PROMPT` — uses `{topic}` + `{notes_payload}`
- `REFLECTION_PROMPT` — uses `{period_label}` + `{notes_payload}`

**Key rule in all prompts:** "Use only note titles and paths that appear below. Do not invent facts."

##### 4.2 Command Registration

Update `commands/__init__.py`:
```python
def register_commands(app: typer.Typer) -> None:
    from vaultmind.commands.brief import brief
    from vaultmind.commands.digest import digest
    ...
    app.command("brief")(brief)
    app.command("digest")(digest)
    ...
```

In `main.py` add:
```python
from vaultmind.commands import register_commands
register_commands(app)
```

##### 4.3 `vm stats` — Vault Health Dashboard (Rich)

**No AI call.** Pure vault scan.

```python
@dataclass(slots=True)
class VaultStats:
    total_notes: int
    vaultmind_notes: int
    notes_this_week: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    top_tags: list[tuple[str, int]]   # top 15
    avg_rating: float | None
    avg_read_time_minutes: float | None
    flashcard_coverage_pct: float
    tagless_note_paths: list[str]
    partial_or_review_paths: list[str]
    moc_candidates: list[tuple[str, int]]  # (tag, count) where count >= 5

def stats(verbose) -> None
def compute_vault_stats(notes, config) -> VaultStats
def render_stats_dashboard(stats: VaultStats) -> None
```

**Rich UI:** summary Panel + tables for type/status/tags/health/MOC candidates.

##### 4.4 `vm find "topic"` — Keyword Search (Textual TUI)

**No AI call.** Uses `search_notes()`.

```python
def find(query: str | None, limit: int = 50, verbose: bool = False) -> None

class FindApp(App[None]):
    # Layout: Header → Input → Horizontal(DataTable, Markdown preview) → Footer
    # Input.Changed triggers search_notes() and updates table
    # Row highlight updates preview pane
    # Empty query shows most recent 20 notes
```

**Table columns:** Score | Title | Tags | Saved | Path

##### 4.5 `vm brief` — Weekly Digest (Rich)

**Uses `fast` tier AI.**

```python
def brief(days: int = 7, limit: int = 20, verbose: bool = False) -> None
```

Pipeline: scan → filter by days → format note packets → `generate_weekly_brief()` → Rich render.

**Rich UI:** takeaway Panel + themes Table + highlights Table + gaps/next steps Panel.

##### 4.6 `vm digest "topic"` — Topic Synthesis (Rich)

**Uses `deep` tier AI.**

```python
def digest(topic: str, limit: int = 15, no_moc: bool = False, verbose: bool = False) -> None
```

Pipeline: scan → `search_notes(topic)` → `generate_topic_digest()` → Rich render → auto-write MOC if `len(matches) >= 5` and `not no_moc`.

**MOC frontmatter:**
```yaml
title: "{Topic} MOC"
vaultmind: true
kind: moc
topic: "{topic}"
generated_by: vm digest
updated: {iso_timestamp}
note_count: {N}
tags: [moc, {topic}]
```

##### 4.7 `vm reflect` — Weekly Mirror (Textual TUI)

**Uses `deep` tier AI.** AI call happens BEFORE launching TUI.

```python
def reflect(days: int = 7, limit: int = 20, verbose: bool = False) -> None
```

Pipeline: scan → filter by days → `generate_reflection()` → launch `ReflectApp`.

**Textual layout:** left OptionList (sections) + right Markdown pane.

Sections: Themes | Belief Shifts | Tensions | Blindspots | Questions | Experiment | Supporting Notes

##### 4.8 `vm flashcard` — Quiz Mode (Textual TUI)

**No AI call in v1.** Reads stored flashcards from saved notes.

```python
def flashcard(topic: str | None = None, limit: int = 30, verbose: bool = False) -> None
```

Pipeline: scan → `collect_flashcard_decks()` → optionally filter by topic → flatten + shuffle → launch `FlashcardApp`.

**Textual layout:** single screen — progress line + center card panel + footer keybindings.

**Keybindings:** `space` flip | `n` next | `p` previous | `k` known | `u` unsure | `q` quit

##### 4.9 Writer Extension

Add to `core/writer.py`:
```python
def write_markdown_page(path: Path, *, body: str, frontmatter: dict | None = None) -> Path
```

For MOC files and any non-source-note markdown. Uses atomic write.

##### 4.10 Dependency Check

Verify `textual` is in `pyproject.toml` dependencies. If not, add it.

##### 4.11 Files to Create/Modify

| File | Action |
|---|---|
| `core/vault_index.py` | **Create** — vault scanning layer |
| `core/search.py` | **Create** — keyword/fuzzy search |
| `core/flashcards.py` | **Create** — flashcard extraction from bodies |
| `core/moc.py` | **Create** — MOC generation helpers |
| `ai/json_utils.py` | **Create** — shared `clean_json_response()` |
| `ai/knowledge.py` | **Create** — AI synthesis (brief/digest/reflect) |
| `ai/prompts.py` | **Modify** — add 4 new prompts |
| `ai/pipeline.py` | **Modify** — use `ai/json_utils.py` |
| `core/writer.py` | **Modify** — add `write_markdown_page()` |
| `commands/__init__.py` | **Modify** — `register_commands()` |
| `main.py` | **Modify** — call `register_commands(app)` |
| `commands/brief.py` | **Implement** |
| `commands/digest.py` | **Implement** |
| `commands/find.py` | **Implement** |
| `commands/flashcard.py` | **Implement** |
| `commands/stats.py` | **Implement** |
| `commands/reflect.py` | **Implement** |
| `pyproject.toml` | **Modify** — ensure `textual` in dependencies |

##### 4.12 Tests to Write

| Test File | Key Test Cases |
|---|---|
| `tests/test_vault_index.py` | scan returns VaultNoteRecords; filters by days; extracts summary; skips non-vaultmind; parses saved_at |
| `tests/test_search.py` | exact title beats body; tag match scores above body; fuzzy handles typos; excerpt around match; empty query returns recent |
| `tests/test_core_flashcards.py` | parses Q/A pairs from body; skips notes without flashcard section; handles malformed pairs |
| `tests/test_core_moc.py` | path uses slug; threshold gating; rendered markdown contains wikilinks |
| `tests/test_knowledge.py` | parse valid brief/digest/reflect JSON; fallback on invalid JSON |
| `tests/test_commands/test_stats.py` | counts by type/status; avg rating; flashcard coverage; tagless detection; MOC candidates |
| `tests/test_commands/test_brief.py` | filters by days; uses fast tier; skips AI when empty |
| `tests/test_commands/test_digest.py` | uses deep tier; writes MOC when threshold met; skips MOC with --no-moc |
| `tests/test_commands/test_flashcard.py` | filters by topic; respects limit; quiz state transitions |
| `tests/test_commands/test_reflect.py` | uses deep tier; filters by days |

---

## Folder Structure (Code)

```
vaultmind/
├── pyproject.toml               ← Project config, dependencies, entry point
├── uv.lock                      ← Locked dependencies with hashes
├── .env                         ← API keys (git-ignored)
├── .env.example                 ← Template for .env
├── config.example.yaml          ← Template for config.yaml
├── ruff.toml                    ← Linter/formatter config
├── README.md
│
├── src/
│   └── vaultmind/
│       ├── __init__.py
│       ├── main.py              ← CLI entry point (typer)
│       ├── config.py            ← Pydantic settings (typed, validated)
│       ├── schemas.py           ← Pydantic models (pipeline contracts)
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── router.py        ← Detects URL type, routes to parser
│       │   ├── scraper.py       ← Article extraction (trafilatura)
│       │   ├── reddit.py        ← Reddit parser
│       │   ├── github.py        ← GitHub parser
│       │   ├── twitter.py       ← Twitter parser
│       │   └── writer.py        ← Writes .md to vault
│       │
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── providers/
│       │   │   ├── __init__.py
│       │   │   ├── base.py      ← Provider protocol (abstract interface)
│       │   │   ├── anthropic.py ← Anthropic/Claude provider
│       │   │   ├── openai.py    ← OpenAI/GPT provider
│       │   │   └── ollama.py    ← Ollama/LM Studio provider (local)
│       │   ├── pipeline.py      ← Main AI processing flow
│       │   ├── prompts.py       ← All AI prompts (provider-agnostic)
│       │   └── linker.py        ← Finds related notes in vault
│       │
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── save.py          ← vm save
│       │   ├── brief.py         ← vm brief
│       │   ├── flashcard.py     ← vm flashcard (Textual)
│       │   ├── find.py          ← vm find (Textual)
│       │   ├── reflect.py       ← vm reflect (Textual)
│       │   ├── stats.py         ← vm stats
│       │   └── digest.py        ← vm digest
│       │
│       └── utils/
│           ├── __init__.py
│           ├── display.py       ← Rich terminal output helpers
│           ├── hashing.py       ← Content hashing for dedup
│           ├── urls.py          ← URL canonicalization & validation
│           └── logging.py       ← Structlog configuration
│
└── tests/
    ├── conftest.py              ← Shared fixtures
    ├── test_router.py
    ├── test_providers.py
    ├── test_pipeline.py
    ├── test_writer.py
    ├── test_schemas.py
    ├── test_urls.py
    └── test_commands/
        └── test_save.py
```

---

## Setup Requirements

Before we start coding, you'll need:

```bash
# 1. Python 3.11 or higher
python3 --version

# 2. uv (modern Python package manager)
# Install: curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version

# 3. An Anthropic API key (and/or OpenAI key)
# Anthropic: https://console.anthropic.com/
# OpenAI: https://platform.openai.com/api-keys

# 4. Your Obsidian vault path (already confirmed)
# /Users/rvs/Obsidian Vault/
```

Your `.env` file (git-ignored, never committed):

```bash
# AI Provider Keys — at least one required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional: GitHub token for higher rate limits
# GITHUB_TOKEN=ghp_...

# Optional: Ollama runs locally, no key needed
# OLLAMA_BASE_URL=http://localhost:11434
```

Your `config.yaml`:

```yaml
vault_path: "/Users/rvs/Obsidian Vault"

folders:
  inbox: "📥 Inbox"
  articles: "📚 Sources"
  tools: "🛠️ Tools"
  threads: "🐦 Threads"
  discussions: "💬 Discussions"
  flashcards: "🃏 Flashcards"          # Future: used when spaced repetition is added
  digests: "📊 Digests"
  mocs: "🗺️ MOCs"
  ideas: "💡 Ideas"
  meta: "⚙️ Meta"
  raw: "📥 Raw"
  wiki: "🗺️ Wiki"
  wiki_concepts: "🧠 Concepts"
  wiki_queries: "📊 Queries"
  wiki_inbox: "📋 Inbox"
  wiki_weekly: "📅 Weekly"
  wiki_index: "📇 Index"

ai:
  default_provider: "anthropic"           # anthropic | openai | ollama
  fallback_chain: ["anthropic", "openai", "ollama"]
  max_tokens: 2000
  generate_flashcards: true
  generate_counterarguments: true
  rating: true
  providers:
    anthropic:
      models:
        fast: "claude-sonnet-4-20250514"
        deep: "claude-opus-4-5"
    openai:
      models:
        fast: "gpt-4.1-mini"
        deep: "gpt-4.1"
    ollama:
      base_url: "http://localhost:11434"
      models:
        fast: "llama3"
        deep: "llama3"

preferences:
  default_status: "processed"
  open_after_save: false
  notify_on_save: true
```

---

## Future Ideas

These aren't in scope now but are worth noting for later:

| Idea | What It Does |
|---|---|
| Browser extension | Right-click any page → "Save to VaultMind" |
| `vm morning` | Daily briefing: what to review, what's connected to what you're thinking about today |
| YouTube support | Transcript → structured notes with timestamps |
| X/Twitter bookmarks sync | Bulk import all your Twitter bookmarks at once |
| Readwise sync | Pull highlights you've already made |
| `vm connect` | Manually tell the AI "this note relates to that note" |
| Spaced repetition | Flashcard review scheduling (like Anki, but in your vault) |
| Voice input | Dictate a thought → becomes a note → AI structures it |
| Newsletter parser | Forward emails to VaultMind → processed into notes |
| Obsidian plugin | Native plugin instead of CLI (long-term goal) |

---

## Philosophy

> *"The goal is not to store more. The goal is to think better."*

VaultMind is built on three principles:

1. **Zero friction capture** — saving something should take one command
2. **Automatic intelligence** — you shouldn't have to organize, the AI should
3. **Resurface over archive** — the vault should bring things back to you, not just store them

The graph view in Obsidian only becomes powerful when notes are connected. VaultMind makes those connections automatically, so your vault becomes a thinking tool rather than a digital filing cabinet.

---

*VaultMind Blueprint v1.5 (FINAL) — Updated: fixed feature/phase label alignment, deterministic folder routing with fixed category enums, Phase 1 provider scope clarified, config.example.yaml added to repo tree. Implementation-ready.*
