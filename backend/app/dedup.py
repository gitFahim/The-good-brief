"""
Deduplication: two articles are the same story if they share a URL, or if
their titles are near-identical after normalization (handles wire-service
stories syndicated with minor title tweaks).
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

TITLE_SIMILARITY_THRESHOLD = 0.85

_PUNCT_RE = re.compile(r"[^\w\s]")
_WS_RE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    t = title.lower()
    t = _PUNCT_RE.sub("", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def is_duplicate(a: dict, b: dict) -> bool:
    """a, b are dicts with at least 'url' and 'title' keys."""
    if a.get("url") and a["url"] == b.get("url"):
        return True
    na, nb = normalize_title(a.get("title", "")), normalize_title(b.get("title", ""))
    if not na or not nb:
        return False
    ratio = SequenceMatcher(None, na, nb).ratio()
    return ratio >= TITLE_SIMILARITY_THRESHOLD


def deduplicate(articles: list[dict]) -> list[dict]:
    """Return articles with duplicates removed, keeping the first occurrence
    (assumes input is already sorted newest-first or by source priority)."""
    kept: list[dict] = []
    for article in articles:
        if not any(is_duplicate(article, existing) for existing in kept):
            kept.append(article)
    return kept
