# VaultMind

> Your personal AI-powered second brain. Feed it anything. Find everything.

A CLI tool that sits between the internet and your [Obsidian](https://obsidian.md) vault. Give it a URL — an article, GitHub repo, Reddit post, or tweet — and it extracts the content, processes it through AI, and writes a beautifully structured, interlinked Markdown note into your vault.

## Quick Start

```bash
# Install
uv pip install -e .

# Configure
cp .env.example .env              # Add your API keys
cp config.example.yaml config.yaml  # Set your vault path

# Save your first note
vm save https://example.com/article
```

## Commands

### `vm save <url>`

The core command. Processes any supported URL through the full pipeline:

1. **Detects** the source type (article, Reddit, GitHub, tweet)
2. **Extracts** clean content (strips ads, nav, tracking params)
3. **Enriches** via AI — summary, key ideas, quotes, counterarguments, tags, rating
4. **Generates** flashcards and finds related notes already in your vault
5. **Writes** an atomic Markdown file with YAML frontmatter to the correct vault folder

```bash
vm save https://github.com/astral-sh/uv
vm save https://www.reddit.com/r/MachineLearning/comments/abc123/some_post
vm save https://example.com/blog/great-article

# Options
vm save <url> --tag cli --tag python   # Add extra tags
vm save <url> --folder "📚 Sources/AI" # Override folder routing
vm save <url> --force                  # Re-process even if already saved
vm save <url> --no-flash               # Skip flashcard generation
vm save <url> --verbose                # Debug logging to stderr
```

**Duplicate detection:** If a URL was already saved, VaultMind skips it (use `--force` to re-process). Passing `--tag` on a duplicate merges the new tags into the existing note.

### `vm find [query]`

Search across all saved notes by keyword or fuzzy match. Without a query, shows recent notes.

```bash
vm find "transformer architecture"
vm find                              # Show recent notes
vm find "rust" --limit 10
```

Scoring weights: exact title match (60), tag match (40), body match (20), plus Jaccard similarity and fuzzy title matching.

### `vm brief`

Generate a weekly digest summarizing what you've saved recently. Uses the **fast** AI tier.

```bash
vm brief              # Last 7 days
vm brief --days 14    # Last 14 days
vm brief --limit 30   # Include up to 30 notes
```

Output includes themes, highlights, gaps in your reading, and suggested next steps.

### `vm digest <topic>`

Deep synthesis on a specific topic across your entire vault. Uses the **deep** AI tier. Automatically generates a Map of Content (MOC) file when 5+ notes match.

```bash
vm digest "AI safety"
vm digest "rust" --no-moc    # Skip MOC generation
vm digest "design" --limit 20
```

### `vm reflect`

A weekly thinking mirror — surfaces patterns, belief shifts, tensions, and blind spots in your saves. Uses the **deep** AI tier.

```bash
vm reflect              # Last 7 days
vm reflect --days 30    # Last 30 days
```

### `vm flashcard`

Quiz yourself on flashcards auto-generated from your saved notes. No AI call needed — cards are parsed from the `## 🃏 Flashcards` section already embedded in each note.

```bash
vm flashcard                    # All cards, shuffled
vm flashcard --topic "AI"       # Filter by topic
vm flashcard --limit 10         # Cap at 10 cards
```

Interactive controls: `space` flip · `n` next · `p` previous · `k` known · `u` unsure · `q` quit

### `vm stats`

Vault health dashboard — total notes, breakdown by type and status, top tags, average rating, flashcard coverage, and MOC candidates.

```bash
vm stats
```

### `vm version`

Show the current VaultMind version.

## Supported Sources

| Source | Extractor | What You Get |
|---|---|---|
| **Articles / Blogs** | [trafilatura](https://github.com/adbar/trafilatura) | Clean text, author, publication, reading time |
| **GitHub Repos** | GitHub REST API | Tool Card format — description, stars, language, README summary |
| **Reddit Posts** | Reddit JSON API | Post + top 5 comments, discussion summary, subreddit as tag |
| **Twitter / X** | Syndication API + trafilatura fallback | Best-effort extraction (experimental, marked as partial on failure) |

## Configuration

### `config.yaml`

```yaml
vault_path: "/path/to/your/Obsidian Vault"

folders:
  inbox: "📥 Inbox"
  articles: "📚 Sources"
  tools: "🛠️ Tools"
  threads: "🐦 Threads"
  discussions: "💬 Discussions"
  # ... see config.example.yaml for all options

ai:
  default_provider: "anthropic"        # anthropic | openai | ollama
  fallback_chain: ["anthropic", "openai", "ollama"]
  max_tokens: 2000
  generate_flashcards: true
  generate_counterarguments: true
  providers:
    anthropic:
      models:
        fast: "claude-sonnet-4-20250514"       # Used by: save, brief
        deep: "claude-opus-4-5"     # Used by: digest, reflect
    openai:
      models:
        fast: "gpt-4.1-mini"
        deep: "gpt-4.1"
```

### `.env`

```bash
# At least one AI provider key is required
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional: higher GitHub API rate limits
GITHUB_TOKEN=ghp_...
```

## Project Structure

```
src/vaultmind/
├── main.py              # CLI entry point (typer)
├── config.py            # Pydantic settings (config.yaml + .env)
├── schemas.py           # Pipeline data models
├── core/
│   ├── router.py        # URL detection & canonicalization
│   ├── extractors.py    # Dispatcher to source-specific extractors
│   ├── scraper.py       # Article extraction (trafilatura)
│   ├── reddit.py        # Reddit JSON API client
│   ├── github.py        # GitHub REST API client
│   ├── twitter.py       # Twitter syndication + fallback
│   ├── renderers.py     # Source-specific Markdown body renderers
│   ├── writer.py        # Atomic vault file writer
│   ├── linker.py        # Related note finder (Jaccard similarity)
│   ├── vault_index.py   # Vault scanner for Phase 4 commands
│   ├── search.py        # Keyword & fuzzy search engine
│   ├── flashcards.py    # Flashcard parser from note bodies
│   └── moc.py           # Map of Content generator
├── ai/
│   ├── pipeline.py      # Content → AIEnrichment flow
│   ├── prompts.py       # All prompt templates (provider-agnostic)
│   ├── knowledge.py     # Brief / Digest / Reflect synthesis
│   ├── json_utils.py    # JSON response cleanup
│   └── providers/       # Anthropic, OpenAI, Ollama (stub)
├── commands/            # One file per CLI command
└── utils/               # Display, hashing, URLs, tags, logging
```

## Tech Stack

- **CLI:** [Typer](https://typer.tiangolo.com) + [Rich](https://rich.readthedocs.io)
- **AI:** Anthropic SDK, OpenAI SDK (provider-agnostic via Protocol)
- **Extraction:** [trafilatura](https://github.com/adbar/trafilatura), [httpx](https://www.python-httpx.org)
- **Data:** [Pydantic](https://docs.pydantic.dev) models, YAML frontmatter
- **Resilience:** [tenacity](https://tenacity.readthedocs.io) retries with exponential backoff
- **Logging:** [structlog](https://www.structlog.org) (JSON to file, human-readable in verbose mode)
- **Package manager:** [uv](https://github.com/astral-sh/uv)

## Requirements

- Python ≥ 3.11
- An Anthropic or OpenAI API key
- An Obsidian vault directory

See [PRD.md](PRD.md) for the full project blueprint.
