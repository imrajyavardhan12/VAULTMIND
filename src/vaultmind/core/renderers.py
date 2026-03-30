"""Source-specific note body renderers."""

from __future__ import annotations

from vaultmind.schemas import (
    AIEnrichment,
    ExtractedContent,
    Flashcard,
    GitHubRepoMetadata,
    RelatedNoteMatch,
    RedditMetadata,
    SourceType,
)


def render_note_body(content: ExtractedContent, enrichment: AIEnrichment) -> str:
    """Dispatch to the appropriate renderer based on source type."""
    match content.source.source_type:
        case SourceType.REDDIT:
            return _render_reddit_body(content, enrichment)
        case SourceType.GITHUB:
            return _render_github_body(content, enrichment)
        case _:
            return _render_article_body(content, enrichment)


def _render_article_body(content: ExtractedContent, enrichment: AIEnrichment) -> str:
    sections = []

    sections.append(f"# {content.title}\n")

    sections.append("## 🧠 Summary")
    sections.append(f"{enrichment.summary}\n")

    sections.append("## 💡 Key Ideas")
    for idea in enrichment.key_ideas:
        sections.append(f"- {idea}")
    sections.append("")

    if enrichment.key_quotes:
        sections.append("## 📌 Key Quotes")
        for quote in enrichment.key_quotes:
            sections.append(f'> "{quote}"')
            sections.append("")

    if enrichment.counterarguments:
        sections.append("## ⚔️ Counterarguments")
        sections.append("*What would a smart critic say about this?*")
        for arg in enrichment.counterarguments:
            sections.append(f"- {arg}")
        sections.append("")

    if content.author or content.site_name:
        sections.append("## 📎 Source Notes")
        if content.author:
            sections.append(f"*Author: {content.author}*")
        if content.site_name:
            sections.append(f"*Publication: {content.site_name}*")
        sections.append("")

    return "\n".join(sections)


def _render_reddit_body(content: ExtractedContent, enrichment: AIEnrichment) -> str:
    meta = content.source_metadata
    sections = []

    sections.append(f"# {content.title}\n")

    # Reddit-specific header
    if isinstance(meta, RedditMetadata):
        sections.append(f"**Subreddit:** r/{meta.subreddit}")
        if meta.post_author:
            sections.append(f"**Posted by:** u/{meta.post_author}")
        if meta.score is not None:
            sections.append(f"**Score:** {meta.score} | **Comments:** {meta.num_comments or '?'}")
        sections.append("")

    sections.append("## 🧠 Discussion Summary")
    sections.append(f"{enrichment.summary}\n")

    sections.append("## 💡 Key Insights")
    for idea in enrichment.key_ideas:
        sections.append(f"- {idea}")
    sections.append("")

    if enrichment.key_quotes:
        sections.append("## 📌 Notable Quotes")
        for quote in enrichment.key_quotes:
            sections.append(f'> "{quote}"')
            sections.append("")

    # Top comments section
    if isinstance(meta, RedditMetadata) and meta.top_comments:
        sections.append("## 💬 Top Comments")
        for i, comment in enumerate(meta.top_comments[:5], 1):
            author = f"u/{comment.author}" if comment.author else "deleted"
            score = f" ({comment.score} pts)" if comment.score is not None else ""
            sections.append(f"**{i}. {author}**{score}")
            # Truncate long comments
            body = comment.body[:500] + "..." if len(comment.body) > 500 else comment.body
            sections.append(f"> {body}")
            sections.append("")

    if enrichment.counterarguments:
        sections.append("## ⚔️ Counterarguments")
        sections.append("*Dissenting views from the discussion:*")
        for arg in enrichment.counterarguments:
            sections.append(f"- {arg}")
        sections.append("")

    return "\n".join(sections)


def _render_github_body(content: ExtractedContent, enrichment: AIEnrichment) -> str:
    meta = content.source_metadata
    sections = []

    sections.append(f"# {content.title}\n")

    # Tool Card header
    if isinstance(meta, GitHubRepoMetadata):
        sections.append("## 🛠️ Tool Card")
        sections.append(f"| Field | Value |")
        sections.append(f"|---|---|")
        if meta.description:
            sections.append(f"| **Description** | {meta.description} |")
        if meta.language:
            sections.append(f"| **Language** | {meta.language} |")
        if meta.stars is not None:
            sections.append(f"| **Stars** | ⭐ {meta.stars:,} |")
        if meta.forks is not None:
            sections.append(f"| **Forks** | 🍴 {meta.forks:,} |")
        if meta.license:
            sections.append(f"| **License** | {meta.license} |")
        if meta.last_pushed_at:
            sections.append(f"| **Last Updated** | {meta.last_pushed_at[:10]} |")
        if meta.homepage:
            sections.append(f"| **Homepage** | [{meta.homepage}]({meta.homepage}) |")
        sections.append("")

    sections.append("## 🧠 Summary")
    sections.append(f"{enrichment.summary}\n")

    sections.append("## 💡 Key Ideas")
    for idea in enrichment.key_ideas:
        sections.append(f"- {idea}")
    sections.append("")

    if enrichment.key_quotes:
        sections.append("## 📌 From the README")
        for quote in enrichment.key_quotes:
            sections.append(f'> "{quote}"')
            sections.append("")

    if enrichment.counterarguments:
        sections.append("## ⚠️ Limitations")
        sections.append("*When NOT to use this:*")
        for arg in enrichment.counterarguments:
            sections.append(f"- {arg}")
        sections.append("")

    if isinstance(meta, GitHubRepoMetadata) and meta.topics:
        sections.append("## 🏷️ Topics")
        sections.append(", ".join(f"`{t}`" for t in meta.topics))
        sections.append("")

    return "\n".join(sections)


def append_note_sections(
    body: str,
    *,
    flashcards: list[Flashcard] | None = None,
    related_notes: list[RelatedNoteMatch] | None = None,
) -> str:
    """Append optional flashcard and related-note sections to a rendered note body."""
    sections: list[str] = []

    if flashcards:
        flashcard_lines: list[str] = ["## 🃏 Flashcards"]
        for flashcard in flashcards:
            flashcard_lines.append(f"**Q:** {flashcard.question}")
            flashcard_lines.append(f"**A:** {flashcard.answer}")
            flashcard_lines.append("")
        sections.append("\n".join(flashcard_lines).rstrip())

    if related_notes:
        related_lines: list[str] = ["## 🔗 Related Notes"]
        for note in related_notes:
            wikilink = f"[[{note.path}|{note.title}]]"
            if note.shared_tags:
                tags = ", ".join(f"`{tag}`" for tag in note.shared_tags)
                related_lines.append(f"- {wikilink} — {tags}")
            else:
                related_lines.append(f"- {wikilink}")
        sections.append("\n".join(related_lines))

    if not sections:
        return body

    return body.rstrip() + "\n\n" + "\n\n".join(sections) + "\n"
