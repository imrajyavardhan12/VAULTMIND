"""All AI prompts — provider-agnostic, source-specific."""

from __future__ import annotations

from vaultmind.schemas import AIEnrichment, ExtractedContent, SourceType

SYSTEM_PROMPT = """You are VaultMind, an AI assistant that processes web content into structured knowledge notes for an Obsidian vault. You are precise, concise, and intellectually honest. You extract real insights, not fluff."""

_JSON_RULES = """Rules:
- key_quotes MUST be exact verbatim text from the content. Do NOT paraphrase or invent quotes.
- tags should be lowercase, specific topics (not generic like "article" or "interesting")
- category MUST be exactly one of: AI, Tech, Philosophy, Business, Science, Design, Misc
- rating is 1-10 based on how useful/insightful the content is
- counterarguments should steelman the opposite view fairly
- Return ONLY valid JSON, no markdown code blocks, no extra text"""

PROCESS_ARTICLE_PROMPT = """Analyze the following article and return a JSON object with these exact fields:

{{
  "summary": "3-5 sentence plain-language summary of the core idea",
  "key_ideas": ["most important point", "second point", "third point with emphasis on what's actionable"],
  "key_quotes": ["exact verbatim quote from the text", "second notable quote if present"],
  "counterarguments": ["the opposite view, steelmanned fairly", "a limitation or blind spot"],
  "tags": ["topic1", "topic2", "topic3", "topic4"],
  "category": "one of: AI, Tech, Philosophy, Business, Science, Design, Misc",
  "rating": 7,
  "read_time_minutes": 12
}}

{json_rules}

- read_time_minutes should be estimated from word count (average 250 words/min)

Title: {title}
Author: {author}
Source: {source}

Content:
{content}"""

PROCESS_REDDIT_PROMPT = """Analyze the following Reddit discussion and return a JSON object with these exact fields:

{{
  "summary": "3-5 sentence summary of the DISCUSSION, not just the original post. Capture the consensus, disagreements, and key insights from comments.",
  "key_ideas": ["main takeaway from the discussion", "most insightful comment perspective", "actionable conclusion"],
  "key_quotes": ["exact verbatim quote from OP or a comment", "second notable quote"],
  "counterarguments": ["strongest dissenting view from the comments", "a limitation acknowledged in the discussion"],
  "tags": ["topic1", "topic2", "subreddit-topic"],
  "category": "one of: AI, Tech, Philosophy, Business, Science, Design, Misc",
  "rating": 7,
  "read_time_minutes": 5
}}

{json_rules}

- Summarize the DISCUSSION, not just the original post
- Include the subreddit topic area in tags
- key_quotes can come from OP or comments but must be verbatim
- read_time_minutes should cover reading OP + key comments

Subreddit: r/{subreddit}
Title: {title}
Author: u/{author}
Source: {source}

Original Post:
{post_text}

Top Comments:
{comments}"""

PROCESS_GITHUB_PROMPT = """Analyze the following GitHub repository and return a JSON object with these exact fields:

{{
  "summary": "3-5 sentences answering: What problem does this solve? Who is it for? How mature is it?",
  "key_ideas": ["core purpose of the tool/library", "key differentiator or unique feature", "practical use case"],
  "key_quotes": ["exact verbatim quote from the README", "second notable quote if present"],
  "counterarguments": ["limitations or when NOT to use this tool", "potential concerns or risks"],
  "tags": ["topic1", "language", "tool-category"],
  "category": "one of: AI, Tech, Philosophy, Business, Science, Design, Misc",
  "rating": 7,
  "read_time_minutes": 5
}}

{json_rules}

- This is a REPOSITORY, not an essay — focus on what it does and whether it's useful
- key_quotes must be exact text from the README only
- Include the programming language and tool category in tags
- counterarguments should be "limitations / when not to use this"
- rating reflects how useful/mature/well-maintained the project appears

Repository: {owner}/{repo}
Language: {language}
Stars: {stars}
Description: {description}
Source: {source}

README:
{content}"""

FLASHCARD_PROMPT = """Create 3-5 flashcards from the note below.
Return ONLY valid JSON in this shape:
{{"flashcards": [{{"question": "...", "answer": "..."}}]}}

Rules:
- Questions should test understanding, not trivia
- Answers should be concise (1-3 sentences)
- Cover core ideas, evidence, and limitations when possible
- Do not include markdown or any text outside JSON

Title: {title}
Summary: {summary}
Key Ideas:
{key_ideas}
Content Excerpt:
{content}
"""

KNOWLEDGE_SYSTEM_PROMPT = """You are VaultMind's synthesis engine.
You must ground every claim in the provided note packets.
Never invent note titles, note paths, facts, dates, or conclusions not supported by the input.
Return only valid JSON matching the requested schema.
"""

WEEKLY_BRIEF_PROMPT = """Create a weekly brief from the note packets below.

Return JSON with this exact shape:
{{
  "period_label": "{period_label}",
  "one_sentence_takeaway": "single high-signal sentence",
  "themes": [{{"name": "theme", "insight": "why it matters"}}],
  "highlights": [{{"title": "exact title", "path": "exact path", "reason": "why notable"}}],
  "gaps": ["what's missing"],
  "suggested_next_steps": ["specific next step"]
}}

Rules:
- Use only note titles and paths that appear below. Do not invent facts.
- Keep output concise and concrete.
- Return JSON only.

Period: {period_label}
Notes:
{notes_payload}
"""

TOPIC_DIGEST_PROMPT = """Create a topic synthesis from the note packets below.

Return JSON with this exact shape:
{{
  "topic": "{topic}",
  "thesis": "single thesis sentence",
  "patterns": ["pattern 1", "pattern 2"],
  "tensions": ["tension 1"],
  "standout_notes": [{{"title": "exact title", "path": "exact path", "reason": "why standout"}}],
  "open_questions": ["question 1"],
  "moc_sections": [{{"heading": "Section", "summary": "one-line summary", "note_paths": ["exact/path"]}}]
}}

Rules:
- Use only note titles and paths that appear below. Do not invent facts.
- Focus on synthesis, not repetition.
- Return JSON only.

Topic: {topic}
Notes:
{notes_payload}
"""

REFLECTION_PROMPT = """Create a reflection report from the note packets below.

Return JSON with this exact shape:
{{
  "period_label": "{period_label}",
  "dominant_themes": ["theme 1", "theme 2"],
  "belief_shifts": ["shift 1"],
  "tensions": ["tension 1"],
  "blindspots": ["blindspot 1"],
  "questions_for_you": ["question 1"],
  "recommended_experiment": "one practical experiment"
}}

Rules:
- Use only note titles and paths that appear below. Do not invent facts.
- Be specific and psychologically useful.
- Return JSON only.

Period: {period_label}
Notes:
{notes_payload}
"""


def build_processing_prompt(content: ExtractedContent) -> str:
    """Build the appropriate processing prompt based on source type."""
    if content.source.source_type == SourceType.REDDIT:
        return _build_reddit_prompt(content)
    if content.source.source_type == SourceType.GITHUB:
        return _build_github_prompt(content)
    return _build_article_prompt(content)


def _build_article_prompt(content: ExtractedContent) -> str:
    return PROCESS_ARTICLE_PROMPT.format(
        json_rules=_JSON_RULES,
        title=content.title,
        author=content.author or "Unknown",
        source=content.source.canonical_url,
        content=content.text,
    )


def _build_reddit_prompt(content: ExtractedContent) -> str:
    from vaultmind.schemas import RedditMetadata

    meta = content.source_metadata
    subreddit = meta.subreddit if isinstance(meta, RedditMetadata) else "unknown"

    # Split text back into post + comments for the prompt
    parts = content.text.split("\n\n--- TOP COMMENTS ---\n\n", 1)
    post_text = parts[0] if parts else content.text
    comments = parts[1] if len(parts) > 1 else "No comments available."

    return PROCESS_REDDIT_PROMPT.format(
        json_rules=_JSON_RULES,
        subreddit=subreddit,
        title=content.title,
        author=content.author or "Unknown",
        source=content.source.canonical_url,
        post_text=post_text,
        comments=comments,
    )


def _build_github_prompt(content: ExtractedContent) -> str:
    from vaultmind.schemas import GitHubRepoMetadata

    meta = content.source_metadata
    if isinstance(meta, GitHubRepoMetadata):
        owner = meta.owner
        repo = meta.repo
        language = meta.language or "Unknown"
        stars = str(meta.stars) if meta.stars is not None else "Unknown"
        description = meta.description or "No description"
    else:
        owner = "unknown"
        repo = "unknown"
        language = "Unknown"
        stars = "Unknown"
        description = "No description"

    return PROCESS_GITHUB_PROMPT.format(
        json_rules=_JSON_RULES,
        owner=owner,
        repo=repo,
        language=language,
        stars=stars,
        description=description,
        source=content.source.canonical_url,
        content=content.text,
    )


def build_flashcard_prompt(content: ExtractedContent, enrichment: AIEnrichment) -> str:
    """Build a focused prompt for flashcard generation."""
    key_ideas = "\n".join(f"- {idea}" for idea in enrichment.key_ideas) or "- None provided"
    content_excerpt = content.text[:6000]
    return FLASHCARD_PROMPT.format(
        title=content.title,
        summary=enrichment.summary,
        key_ideas=key_ideas,
        content=content_excerpt,
    )


def build_weekly_brief_prompt(*, period_label: str, notes_payload: str) -> str:
    return WEEKLY_BRIEF_PROMPT.format(period_label=period_label, notes_payload=notes_payload)


def build_topic_digest_prompt(*, topic: str, notes_payload: str) -> str:
    return TOPIC_DIGEST_PROMPT.format(topic=topic, notes_payload=notes_payload)


def build_reflection_prompt(*, period_label: str, notes_payload: str) -> str:
    return REFLECTION_PROMPT.format(period_label=period_label, notes_payload=notes_payload)


# ---- vm compile prompts ----

COMPILE_CONCEPT_TRIAGE_PROMPT = """You are a librarian organizing a research wiki.

Given the following RAW source documents (these are the original texts, NOT AI summaries), identify the key concepts they introduce or substantially advance.

For each concept:
- Determine if it is [NEW], [EXISTING: concept-slug], or [MERGE: concept-slug]
- Provide a one-line description of the concept
- List the source URLs that inform this concept
- If EXISTING or MERGE, use the exact concept slug provided

Respond ONLY with valid JSON in this exact shape:
{{"concepts": [{{"name": "concept name", "status": "new|existing:slug|merge:slug", "description": "one-line description", "source_urls": ["url1", "url2"], "merge_target": "slug if MERGE, else null"}}]}}

Rules:
- Slugs must be lowercase, hyphenated (e.g. "attention-mechanisms")
- Do not invent URLs — only use the source URLs provided below
- If multiple sources cover the same concept, mark them MERGE with the most representative slug
- Be conservative: only create a new concept if it genuinely warrants its own article
- READ the full content of each source before assigning a concept

Sources:
{new_sources}
"""


COMPILE_ARTICLE_CREATE_PROMPT = """Write a new wiki article for the concept "{concept_name}".

Description: {description}
Sources to synthesize: {source_urls}

The article should:
- Be 400-800 words
- Have clear sections: Overview, Key Ideas, Sources
- Include a Sources section with full URLs, listed in order of importance
- Be written in an encyclopedic but accessible tone
- Use wikilinks for related concepts you know about (e.g. [[attention-mechanisms]])
- Do NOT repeat exact quotes from sources — synthesize in your own words

Write the article in full markdown. No frontmatter. No code blocks unless showing code.
"""


COMPILE_ARTICLE_UPDATE_PROMPT = """You are maintaining a research wiki. Update the existing wiki article to incorporate new information from the listed sources.

Existing article:
---
{existing_content}
---

New sources to incorporate:
{new_sources}

Rules:
- Update the article to incorporate all new information
- Maintain consistent structure and tone with the existing article
- Add new backlinks to related concepts where appropriate (e.g. [[attention-mechanisms]])
- Be 400-800 words unless the new sources substantially expand the topic
- Keep the Sources section updated — add new URLs at the bottom
- Do NOT repeat exact quotes — synthesize in your own words

Write the updated article in full markdown. No frontmatter.
"""


COMPILE_INDEX_REBUILD_PROMPT = """You are maintaining a wiki index. Rebuild the master index file based on the current state of the wiki.

Existing index (for reference):
---
{existing_index}
---

Current wiki articles:
{article_summaries}

Rules:
- Keep the index concise — one line per concept with a brief description
- Note any orphan concepts (concepts with no links from other articles)
- Keep the structure clean and alphabetically ordered
- Use Obsidian wikilink syntax for article links: [[slug|display text]]
- IMPORTANT: Preserve wikilinks as [[...]] not **bold text**

Write the updated index in full markdown. No frontmatter.
"""

COMPILE_CONCEPT_DEDUP_PROMPT = """You are a librarian deduplicating a concept list. Given a list of concepts identified from raw sources, merge overlapping or near-duplicate concepts into a single canonical entry.

Concepts to deduplicate:
{concepts}

Rules:
- Merge concepts that cover the same or substantially overlapping territory
- When merging, pick the most descriptive name as the canonical name
- Combine descriptions into one coherent summary
- Combine all source_urls from merged entries
- Preserve status whenever a merged concept includes an existing or merge target
- Use status exactly as "new", "existing:slug", or "merge:slug"
- Keep genuinely distinct concepts separate
- Return ALL concepts (merged and unique) in the same JSON format

Return ONLY valid JSON:
{{"concepts": [{{"name": "canonical name", "status": "new|existing:slug|merge:slug", "description": "combined description", "source_urls": ["url1", "url2"], "merge_target": "slug if merge/existing, else null"}}]}}
"""
