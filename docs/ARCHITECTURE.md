# VaultMind: Architecture Evolution Plan

> *"I think there is room here for an incredible new product instead of a hacky collection of scripts."*
> — Andrej Karpathy

## Context

VaultMind is built on **Karpathy's LLM Wiki pattern** as described in his [llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

The core insight: most personal knowledge tools treat LLMs as retrieval engines (RAG). The better pattern is to have the LLM **incrementally build and maintain a persistent wiki** between you and your raw sources. The wiki is a compounding artifact — every source you add and every question you ask makes the next ones richer.

> *"The knowledge is compiled once and then kept current, not re-derived on every query."*

---

## The Three-Layer Architecture

Karpathy defines three distinct layers, each with a specific purpose:

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: RAW SOURCES — immutable, LLM reads but never writes │
│                                                                 │
│  Your curated collection of original source documents.          │
│  Articles, papers, images, data files.                          │
│  This is your source of truth.                                  │
│                                                                 │
│  How to populate: Obsidian Web Clipper browser extension       │
│  saves articles as .md directly to this folder.                  │
└─────────────────────────────────────────────────────────────────┘
                              ↑ LLM reads from here
                              ↓ LLM writes to here
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: WIKI — LLM-authored, LLM owns entirely               │
│                                                                 │
│  Summaries, entity pages, concept pages, comparisons.           │
│  The LLM creates pages, updates them when new sources arrive,   │
│  maintains cross-references, keeps everything consistent.        │
│  You read it; the LLM writes it.                                │
└─────────────────────────────────────────────────────────────────┘
                              ↑ LLM reads wiki for context
                              ↓ LLM writes answers back here
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: SCHEMA — the configuration that disciplines the LLM    │
│                                                                 │
│  A document (e.g. CLAUDE.md) that tells the LLM how the wiki   │
│  is structured, what conventions to follow, and what workflows  │
│  to use when ingesting sources, answering questions, or         │
│  maintaining the wiki.                                          │
│                                                                 │
│  This is the key configuration file. You and the LLM co-evolve  │
│  it over time as you figure out what works for your domain.     │
└─────────────────────────────────────────────────────────────────┘
```

**Critical invariant:** Raw sources are **immutable**. The LLM never modifies them. This is what makes the wiki trustworthy — the raw layer is always the ground truth.

---

## VaultMind's Two Active Layers

Karpathy's Raw Sources layer is managed **outside VaultMind** (via Obsidian Web Clipper). VaultMind owns two layers:

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: 📥 RAW/ (external)                                    │
│  Immutable source documents saved by Obsidian Web Clipper.       │
│  VaultMind reads from here during vm compile.                    │
│  Humans manage this folder — VM never writes to it.              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: 🗺️ WIKI/ (VM-owned)                                   │
│  LLM-authored concept articles, queries, digests.                │
│  Written and maintained by vm compile and vm ask.                │
└─────────────────────────────────────────────────────────────────┘
```

VaultMind **does not** use a `Sources/` folder in the wiki compilation path. The `vm save` command (which creates structured personal notes with AI summaries) is a **separate workflow** — it's your personal reading notes, not the raw compilation layer.

---

## The Three Loops

Karpathy's system runs three distinct operations. VaultMind implements them as:

```
┌─────────────────────────────────────────────────────────────────┐
│  OPERATION 1: INGEST                                             │
│  How: Obsidian Web Clipper (external tool, not VaultMind)        │
│  What: Save original web articles as .md to 📥 Raw/              │
│  Key: Raw sources are immutable once saved                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  OPERATION 2: COMPILE (vm compile) — IMPLEMENTED                │
│  What: 📥 Raw/ → 🗺️ Wiki/🧠 Concepts/                           │
│  LLM reads raw sources, synthesizes wiki concept articles        │
│  Runs: manually after adding new raw sources                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  OPERATION 3: QUERY (vm ask) — PLANNED                          │
│  What: Question → search Wiki + Raw → answer → Wiki/📊 Queries/ │
│  The compound interest engine. Every answer files back to wiki.  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Wiki Directory Structure

```
{vault_root}/
├── 📥 Raw/                        ← Layer 1: Original sources (Obsidian Web Clipper)
│   ├── attention-is-all-you-need.md   (immutable, VM reads only)
│   ├── flash-attention.md
│   └── rlhf-tutorial.md
│
├── 🗺️ Wiki/                      ← Layer 2: LLM-authored wiki (VM owns)
│   ├── 🧠 Concepts/              ← Concept articles (compiled from Raw/)
│   │   ├── attention-mechanisms.md
│   │   ├── transformers.md
│   │   └── rlhf.md
│   ├── 📊 Queries/               ← Answers filed from vm ask (the flywheel)
│   │   └── what-is-the-difference-between-rlhf-and-dpo.md
│   ├── 📋 Inbox/                ← Lint triage + reflections
│   │   ├── lint-2026-04-03.md
│   │   └── reflect-2026-04.md
│   ├── 📅 Weekly/                ← Compiled briefs
│   │   └── brief-2026-W14.md
│   ├── 📇 Index.md               ← Master concept index (updated on every compile)
│   └── 📋 Log.md                 ← Chronological append-only record
│
├── 📚 Sources/                    ← Personal notes (separate workflow)
│   ├── AI/                       ← vm save creates structured notes here
│   ├── Tech/                     ← These are NOT used in compile loop
│   └── ...
│
└── vault.manifest.json           ← Tracks: which Raw sources → which Wiki articles
```

**Key distinction:**
- `📥 Raw/` → feeds `vm compile` → produces `🗺️ Wiki/🧠 Concepts/`
- `📚 Sources/` → personal annotated bookmarks from `vm save` → **not** part of the compile loop
- Both are searchable by `vm find` and `vm ask`

---

## Compilation: Raw → Wiki

The `vm compile` command is the core of the system. It reads from `📥 Raw/` and writes to `🗺️ Wiki/🧠 Concepts/`.

### The Current Problem (Fixed)

**The original architecture had a critical flaw:** `vm compile` was reading from `📚 Sources/` (AI-enriched personal notes) instead of `📥 Raw/` (original source documents). This meant:

```
❌ WRONG:  Sources/ (AI summary) → vm compile → Wiki/
✅ RIGHT:  Raw/ (original text) → vm compile → Wiki/
```

The LLM was summarizing summaries. Karpathy's pattern requires the compile step to read **original source content** so the LLM can synthesize fresh understanding, not re-summarize what it already summarized.

### How Compile Works

```
1. Read vault.manifest.json
2. Scan 📥 Raw/ for new or changed files (by content hash)
3. For each new/changed raw source:
   a. LLM reads the original content
   b. Concept extraction: what concepts does this source introduce?
   c. For each concept:
      - Existing wiki article? → Update pass (read article + new source → updated article)
      - New concept? → Create pass (write new article from scratch)
   d. Update manifest: source URL → wiki article(s) mapping
4. Rebuild Wiki/📇 Index.md
```

**Karpathy's insight:** The first few sources are hard to categorize. The 50th source is trivially filed because the wiki structure exists. The marginal cost of each new source decreases over time.

### Compile Prompts (in `ai/prompts.py`)

```python
# Stage 1: Concept triage
COMPILE_CONCEPT_TRIAGE_PROMPT = """
You are a librarian organizing a research wiki. Given the following RAW source documents
(these are the original texts, NOT summaries), identify the key concepts.

For each concept:
- Determine if it is [NEW], [EXISTING: concept-slug], or [MERGE: concept-slug]
- Provide a one-line description
- List the source URLs that inform this concept

Sources:
{raw_sources}
"""

# Stage 2: Article create
COMPILE_ARTICLE_CREATE_PROMPT = """
Write a new wiki article for the concept "{concept_name}".
Description: {description}
Sources: {source_urls}

Write 400-800 words in encyclopedic but accessible tone.
Include a Sources section with full URLs.
"""

# Stage 2: Article update
COMPILE_ARTICLE_UPDATE_PROMPT = """
Update this wiki article with new information from the sources.
Maintain structure and tone. Add backlinks to related concepts.
"""
```

---

## Query: Wiki → Better Wiki

The `vm ask` command is the compound interest engine.

```
Question → Search Wiki + Raw → LLM synthesizes → Answer filed to Wiki/📊 Queries/
                                                         ↓
                                    Future questions read this answer
```

**Key flywheel:** Answers filed back to the wiki make future queries smarter. The knowledge base compounds.

### The Three Operations

```
┌─────────────────────────────────────────────────────────────────┐
│  INGEST — External (Obsidian Web Clipper)                       │
│  Save original web articles to 📥 Raw/ as .md files             │
│  These are immutable. Never modified by VaultMind.               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  COMPILE (vm compile) — IMPLEMENTED                            │
│  📥 Raw/ → 🗺️ Wiki/🧠 Concepts/                               │
│  LLM reads original source content, writes concept articles      │
│  Incremental: only new/changed Raw/ files trigger recompilation  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  QUERY (vm ask) — PLANNED                                      │
│  Question → search Wiki + Raw → LLM → answer → Wiki/📊 Queries/ │
│  Every answer compounds into the wiki for future queries         │
└─────────────────────────────────────────────────────────────────┘
```

---

## vm compile — Deep Dive

### Manifest Tracking

The manifest maps raw source URLs → wiki article slugs:

```json
{
  "version": 1,
  "last_compiled": "2026-04-03T10:00:00Z",
  "raw_sources": {
    "https://example.com/article": {
      "raw_file": "📥 Raw/attention-is-all-you-need.md",
      "content_hash": "a3f2b1",
      "compiled_at": "2026-04-03T10:00:00Z",
      "wiki_articles": ["attention-mechanisms", "transformer-architecture"]
    }
  },
  "wiki_articles": {
    "attention-mechanisms": {
      "last_updated": "2026-04-03T10:00:00Z",
      "source_urls": ["https://example.com/article"],
      "content_hash": "c4d3e2"
    }
  }
}
```

**Key behavior:** `vm compile` diffs content hashes of files in `📥 Raw/` against the manifest. Only new or changed files trigger recompilation.

### Compilation Modes

**Early stage (< 10 sources, human in the loop):**
```
$ vm compile
New: "Attention Is All You Need"
Concept extraction: [attention, transformers, self-attention]
No existing articles. Creating:
  → 🗺️ Wiki/🧠 Concepts/attention.md [NEW]
  → 🗺️ Wiki/🧠 Concepts/transformers.md [NEW]
Human review: [y/n/edit] →
```

**Late stage (10+ sources, autonomous):**
```
$ vm compile
New: "Flash Attention"
Concept extraction: [flash-attention, attention, transformers]
Existing articles found:
  → 🗺️ Wiki/🧠 Concepts/attention.md [UPDATE]
Auto-updating (safe because content_hash changed).
```

### Compile Prompts (in `ai/prompts.py`)

```python
# Stage 1: Concept triage
COMPILE_CONCEPT_TRIAGE_PROMPT = """
You are a librarian organizing a research wiki. Given the following RAW source documents
(these are the original texts, NOT summaries), identify the key concepts.

For each concept:
- Determine if it is [NEW], [EXISTING: concept-slug], or [MERGE: concept-slug]
- Provide a one-line description
- List the source URLs that inform this concept

Sources:
{raw_sources}
"""

# Stage 2: Article create
COMPILE_ARTICLE_CREATE_PROMPT = """
Write a new wiki article for the concept "{concept_name}".
Description: {description}
Sources: {source_urls}

Write 400-800 words. Sections: Overview, Key Ideas, Sources.
Include full URLs in Sources section.
"""

# Stage 2: Article update
COMPILE_ARTICLE_UPDATE_PROMPT = """
Update this wiki article with new information from the sources.
Maintain structure and tone. Add backlinks to related concepts.
"""
```

---

## vm ask — Deep Dive

**The compound interest engine.**

```
Question → Search Wiki + Raw → LLM → Answer → Wiki/📊 Queries/
                                          ↓
                          Future questions read this answer
```

**Implementation:** Thin agent loop using existing `search.py` and `vault_index.py` as tools. No LangChain.

```python
MAX_ITERATIONS = 3

for i in range(MAX_ITERATIONS):
    context = _build_context(question, gathered_sources, gathered_wiki)
    response = provider.complete(system_prompt, user_prompt.format(
        question=question, context=context
    ))
    
    needs = _extract_gaps(response)  # LLM self-assessment
    if not needs or i == MAX_ITERATIONS - 1:
        _file_answer(...)  # Write to Wiki/📊 Queries/
        break
    
    for gap in needs:
        more = search_notes(gap)
        gathered_sources.update(more)
```

---

## vm lint — Health Checks

Health checks output to `🗺️ Wiki/📋 Inbox/lint-YYYY-MM-DD.md`.

```python
LINT_CHECKS = {
    "orphan_raw_sources": "Raw files never compiled into any wiki article",
    "orphan_wiki_articles": "Wiki articles with no incoming links",
    "concept_gaps": "Raw source clusters with no wiki article",
    "stale_articles": "Wiki articles not updated despite new raw sources",
}
```

---

## vm brief / vm reflect — Evolve to Wiki

These commands currently output to terminal. Target: write to wiki.

```
vm brief --wiki     → 🗺️ Wiki/📅 Weekly/brief-YYYY-Www.md
vm reflect --wiki   → 🗺️ Wiki/📋 Inbox/reflect-YYYY-MM.md
```

Both still support `--preview` to print to stdout.

---

## Wiki Navigation: Index and Log

Karpathy specifies two special files that help navigate the wiki as it grows.

### 📇 Index.md — Content Catalog

Updated on every `vm compile`. A catalog of every wiki page.

```
# Wiki Index

## Concepts
- [[attention-mechanisms]] — Self-attention and its variants (3 sources)
- [[transformers]] — Neural network architecture built on attention (2 sources)
- [[rlhf]] — Reinforcement learning from human feedback (4 sources)

## Queries
- [[what-is-the-difference-between-rlhf-and-dpo]] — 2026-04-03
- [[attention-bottleneck-analysis]] — 2026-04-01
```

**How it's used:** When `vm ask` runs, it reads the index first to find relevant pages, then drills into them. This avoids needing embeddings at small scale (~100 sources).

### 📋 Log.md — Chronological Record

Append-only log of everything that happened.

```
## [2026-04-07] compile | Added flash-attention.md
## [2026-04-06] ask | what is the relationship between rlhf and constitutional ai?
## [2026-04-05] lint | ran full health check
## [2026-04-04] ingest | added transformers paper via Web Clipper
```

**Format rule:** Each entry starts with `## [YYYY-MM-DD]`. This makes it grep-able:
```bash
grep "^## \[" Wiki/📋\ Log.md | tail -5  # last 5 entries
```

The log gives the LLM context about what's been done recently without having to scan the entire wiki.

---

## CLI Tools

Karpathy suggests building small tools to help the LLM operate on the wiki.

### Search

At small scale, the index file is enough. As the wiki grows, a proper search engine helps.

**Recommended:** [qmd](https://github.com/tobi/qmd) — local search engine for markdown with BM25/vector hybrid + LLM re-ranking. Has both CLI and MCP server.

**Fallback:** A naive grep-based search is fine for < 100 wiki pages. The existing `vm find` command covers this.

### Future Tools to Consider

| Tool | Purpose |
|------|---------|
| `qmd` | Full-text search with embeddings (optional, at scale) |
| Custom backlink updater | Re-scans all wiki pages to fix broken wikilinks |
| Source URL validator | Checks if Raw/ sources are still accessible |

These are **not in scope** for v1-v2. The index file + grep is sufficient until ~100 wiki pages.

---

## Tips and Tricks (Obsidian Workflow)

These are Karpathy's recommended practices for getting the most out of the system.

### 1. Obsidian Web Clipper — Ingest
Browser extension that converts web articles to markdown. Install it, configure it to save to `📥 Raw/` subfolder, and use it as the primary way to capture sources.

### 2. Download Images Locally
After clipping an article:
1. Obsidian → Settings → Files and Links → Attachment folder path → `📥 Raw/assets/`
2. Settings → Hotkeys → Search "Download" → Bind to `Ctrl+Shift+D`
3. After clipping, hit `Ctrl+Shift+D` to download all images locally

**Why:** LLMs can reference local images. URLs may break over time. Local images are stable.

### 3. Obsidian Graph View
View → Show graph. This shows the shape of your wiki — what's connected, which pages are orphans. Useful for identifying concept gaps and over-connected hub pages.

### 4. Marp — Slide Decks
VaultMind can generate Marp slides from wiki content (`vm digest --format slides`). Obsidian has a Marp plugin for rendering.

### 5. Dataview — Dynamic Queries
Obsidian Dataview plugin runs queries over frontmatter. If wiki pages have YAML frontmatter (tags, dates, source counts), Dataview can generate dynamic tables. VaultMind wiki pages don't require frontmatter, but adding it helps Dataview users.

### 6. Git — Version History
The wiki is just a git repo of markdown files. You get version history, branching, and collaboration for free. Commit regularly.

```
cd ~/path/to/vault
git add .
git commit -m "compiled 3 new sources on RLHF"
```

---

## The Schema (CLAUDE.md)

Karpathy's Layer 3: A document that tells the LLM how to maintain the wiki.

Stored in the vault root as `CLAUDE.md` (for Claude Code) or `AGENTS.md` (for Codex). It evolves with you.

**Example structure:**

```markdown
# Vault Wiki Schema

## Purpose
This is a personal research wiki on machine learning.
The LLM compiles sources into concept articles and answers questions.

## Conventions

### Article structure
- Overview: 1-2 paragraph introduction
- Key Ideas: 3-5 bullet points
- Sources: full URLs listed in order of importance

### Wikilinks
- Use [[slug|Display Title]] format
- Create red links for concepts that don't exist yet (they resolve later)

### Compiling
- Run `vm compile` after adding 3-5 new Raw/ sources
- Review early-stage articles (first 10 sources) manually
- Let the LLM run autonomously after the structure stabilizes

### Asking questions
- File good answers back to Wiki/📊 Queries/
- Link answers from relevant concept articles
- Use `--preview` to check before filing
```

The schema is human-edited. Every time you discover a better convention, add it to CLAUDE.md.

---

## Karpathy's "Team of LLMs" Vision

> *"In the natural extrapolation, you could imagine that every question spawns a team of LLMs to automate the whole thing: iteratively construct an entire ephemeral wiki, lint it, loop a few times, then write a full report."*

This is beyond the current scope but worth noting as a design horizon:

```
User question
    ↓
[Orchestrator LLM]
    ├── [Compiler LLM]    → builds ephemeral wiki for this question
    ├── [Critic LLM]     → lint check on ephemeral wiki
    ├── [Reporter LLM]  → writes final report from ephemeral wiki
    ↓
Final report → filed to Wiki/📊 Queries/ + linked to concepts
```

This is v3 territory. The compile loop and ask loop in v1/v2 are the necessary precursors.

---

## What NOT to Add

Explicitly rejecting these to preserve simplicity:

| Rejected | Reason |
|----------|--------|
| **Vector database / embeddings** | Karpathy explicitly says it's not needed at this scale. The manifest + greedy search + LLM context is sufficient until 500+ sources. |
| **SQLite / any database** | Plain JSON manifest. Human-readable, version-controllable, zero dependency. |
| **LangChain / LlamaIndex** | 100 lines of custom agent loop is cleaner than another framework. |
| **PDF extractor as first-class** | URL → markdown is the core loop. PDFs are edge case. Add later if demand is real. |
| **Image ingestion** | Same reasoning. First make the text loop work. |
| **Watch daemon** | Changes the product from CLI to background service. Validate the workflow manually first. |
| **sentence-transformers** | Heavy local dependency. Semantic similarity is a nice-to-have, not necessary. |

---

## Implementation Sequence

### ✅ Phase 1 — Foundation
```
vm compile              # reads 📥 Raw/, writes 🗺️ Wiki/
vm compile --full      # full rebuild: all Raw/ files
vm compile --dry-run   # preview without writing
```

**Files implemented:**
- `core/manifest.py` — manifest read/write/upsert/diff
- `ai/compiler.py` — 3-stage pipeline: concept triage → create/update articles → rebuild index
- `commands/compile.py` — CLI with `--full`, `--dry-run`, `--verbose`
- `schemas.py` — `Manifest`, `ManifestSource`, `ManifestWikiEntry`, `WikiConceptEntry`, `ConceptStatus`
- `config.py` — wiki folder paths
- `ai/prompts.py` — compile prompts

**Status:** Infrastructure complete. `vm compile` now reads from `📥 Raw/` by default, with a compatibility fallback to legacy `Clippings/` vaults when `📥 Raw/` is absent.

### Phase 2 — Query (vm ask)
```
vm ask <question>           # agent loop, output to Wiki/Queries/
vm ask <question> --preview  # print to stdout without filing
```
- `ai/asker.py` — thin agent loop, max 3 iterations, gap-following
- `commands/ask.py` — `--depth shallow|deep`, `--preview`

### Phase 3 — Health (vm lint)
```
vm lint              # output to Wiki/Inbox/
vm lint --checks ... # orphan|gaps|stale|all
```
- `ai/linter.py` — orphan raw sources, concept gaps, stale articles
- `commands/lint.py` — `--checks`, `--output`

### Phase 4 — Evolve vm brief / vm reflect
```
vm brief --wiki     → 🗺️ Wiki/📅 Weekly/
vm reflect --wiki   → 🗺️ Wiki/📋 Inbox/
```

### Phase 5 — Output formats
```
vm digest --format slides  # Marp
vm digest --format chart    # matplotlib PNG
```

---

## Key Design Decisions

1. **Three-layer architecture.** `📥 Raw/` (immutable sources) → `🗺️ Wiki/` (LLM-authored) → `📚 Sources/` (personal notes). Each has a distinct purpose.

2. **Raw sources are immutable.** The LLM never modifies `📥 Raw/`. This is the ground truth. Compiling the same raw source twice always produces the same wiki article.

3. **`vm compile` reads from 📥 Raw/, not 📚 Sources/.** This is critical. The compile step synthesizes from original source content, not AI summaries. This is what makes the wiki valuable.

4. **Manifest is a file, not a database.** Plain JSON. Version-controllable. Human-readable. No schema migrations.

5. **`vm ask` files output to wiki.** Every answer compounds into the knowledge base for future queries.

6. **Lint outputs to inbox, not terminal.** Human reviews, LLM proposes. The inbox never auto-applies changes.

7. **No agent framework.** A thin agent loop using existing `search.py` and `vault_index.py`. No LangChain.

---

## Summary

VaultMind follows Karpathy's LLM Wiki pattern:

```
📥 Raw/ (Obsidian Web Clipper)  →  vm compile  →  🗺️ Wiki/
                                                     ↓
                                              vm ask
                                                     ↓
                                         🗺️ Wiki/📊 Queries/
```

**Architecture:**
- `📥 Raw/` — immutable source documents (managed externally by Obsidian Web Clipper)
- `🗺️ Wiki/` — LLM-authored concept articles (written by `vm compile`)
- `📚 Sources/` — personal annotated bookmarks (written by `vm save`)

**What `vm compile` does:**
- Reads original content from `📥 Raw/`
- Synthesizes wiki concept articles in `🗺️ Wiki/🧠 Concepts/`
- Tracks source → article mappings in `vault.manifest.json`

**What `vm ask` does:**
- Answers questions by searching wiki + raw sources
- Files answers back to `🗺️ Wiki/📊 Queries/`
- Makes the knowledge base compound over time

**Current status:**
- `vm compile` reads from `📥 Raw/` by default and writes to `🗺️ Wiki/🧠 Concepts/`
- `vm compile --dry-run` previews raw sources and concept targets without writing
- `vm ask`, `vm lint`, `vm brief --wiki`, `vm reflect --wiki` still to build

---

## Validation Checklist

**Phase 1 (vm compile):**
- [x] `vm compile` reads from `📥 Raw/` (not `📚 Sources/`)
- [x] Manifest tracks Raw/ content hashes correctly
- [x] `vm compile --dry-run` shows planned changes without writing
- [ ] Wiki/🧠 Concepts/ articles are created/updated correctly
- [ ] Wiki/📇 Index.md is updated after each compile

**Phase 2 (vm ask):**
- [ ] `vm ask "question"` searches both Wiki/ and Raw/
- [ ] Answer is filed to Wiki/📊 Queries/
- [ ] `vm ask --preview` prints without filing

**Phase 3 (vm lint):**
- [ ] `vm lint` creates Wiki/📋 Inbox/lint-YYYY-MM-DD.md
- [ ] Orphan Raw/ sources are correctly identified

**Phase 4 (vm brief / vm reflect):**
- [ ] Both commands write to Wiki/ by default
- [ ] Both support `--preview` for terminal output

---

## Dependencies

No new dependencies. Everything is implemented with existing stack:
- `httpx`, `anthropic`/`openai`, `tenacity`, `pydantic`, `typer`
