"""URL canonicalization and validation."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "ref",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "s",
    "si",
    "feature",
}

DOMAIN_NORMALIZATIONS: dict[str, str] = {
    "mobile.twitter.com": "x.com",
    "twitter.com": "x.com",
    "www.twitter.com": "x.com",
    "mobile.x.com": "x.com",
    "old.reddit.com": "www.reddit.com",
    "np.reddit.com": "www.reddit.com",
    "i.reddit.com": "www.reddit.com",
    "m.reddit.com": "www.reddit.com",
}


def canonicalize_url(url: str) -> str:
    """Canonicalize a URL by stripping tracking params, normalizing domains, etc."""
    parsed = urlparse(url.strip())

    scheme = parsed.scheme or "https"
    hostname = (parsed.hostname or "").lower()

    hostname = DOMAIN_NORMALIZATIONS.get(hostname, hostname)

    if hostname.startswith("www.") and hostname not in ("www.reddit.com",):
        hostname = hostname[4:]

    query_params = parse_qs(parsed.query, keep_blank_values=False)
    filtered_params = {
        k: v for k, v in sorted(query_params.items()) if k.lower() not in TRACKING_PARAMS
    }
    clean_query = urlencode(filtered_params, doseq=True)

    path = parsed.path.rstrip("/") or ""

    # Strip fragments
    canonical = urlunparse((scheme, hostname, path, "", clean_query, ""))
    return canonical


def detect_source_type(url: str) -> str:
    """Detect the source type from a URL."""
    from vaultmind.schemas import SourceType

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    # Normalize for detection
    hostname = DOMAIN_NORMALIZATIONS.get(hostname, hostname)
    if hostname.startswith("www."):
        hostname = hostname[4:]

    if hostname in ("x.com", "twitter.com"):
        return SourceType.TWEET

    if hostname in ("reddit.com", "www.reddit.com"):
        return SourceType.REDDIT

    if hostname == "github.com":
        return SourceType.GITHUB

    if hostname in ("youtube.com", "youtu.be", "m.youtube.com"):
        return SourceType.VIDEO

    return SourceType.ARTICLE
