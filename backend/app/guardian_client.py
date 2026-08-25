"""Thin client for the Guardian Content API.

Kept deliberately simple: fetch a page of recent articles and normalize
each into the flat dict shape the rest of the pipeline expects
(url, title, summary, section, image_url, published_at).
"""
from __future__ import annotations

from datetime import datetime

import httpx

from app.config import GUARDIAN_API_KEY, GUARDIAN_API_URL


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_articles(page_size: int = 50, query: str | None = None) -> list[dict]:
    """Fetch and normalize a page of articles from the Guardian API.

    Raises httpx.HTTPError on network/API failure -- callers should catch
    and log, not crash the whole ingestion run.
    """
    params = {
        "api-key": GUARDIAN_API_KEY,
        "page-size": page_size,
        "show-fields": "trailText,thumbnail",
        "order-by": "newest",
    }
    if query:
        params["q"] = query

    with httpx.Client(timeout=15.0) as client:
        response = client.get(GUARDIAN_API_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    results = payload.get("response", {}).get("results", [])
    normalized = []
    for item in results:
        fields = item.get("fields", {}) or {}
        normalized.append({
            "url": item.get("webUrl", ""),
            "title": item.get("webTitle", ""),
            "summary": fields.get("trailText", ""),
            "section": item.get("sectionName", ""),
            "image_url": fields.get("thumbnail", ""),
            "published_at": _parse_date(item.get("webPublicationDate")),
        })
    return normalized
