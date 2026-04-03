"""Shared JSON response cleanup for AI providers."""

from __future__ import annotations


def clean_json_response(response: str) -> str:
    """Clean fenced/annotated JSON responses into plain JSON text."""
    cleaned = response.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()

    return cleaned
