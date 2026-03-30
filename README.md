# VaultMind

> Your personal AI-powered second brain. Feed it anything. Find everything.

A CLI tool that processes URLs (articles, GitHub repos, Reddit posts) through AI and saves beautifully structured notes to your Obsidian vault.

## Quick Start

```bash
# Install
uv pip install -e .

# Configure
cp .env.example .env        # Add your API keys
cp config.example.yaml config.yaml  # Set your vault path

# Use
vm save https://example.com/article
```

See [PRD.md](PRD.md) for the full project blueprint.
