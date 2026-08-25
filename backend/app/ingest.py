"""
Ingestion pipeline: fetch -> dedup (against DB + within batch) -> classify
-> filter to positive-only -> store.

Exposed as a single `run_ingestion` function so it can be called from a CLI
entry point, a cron job, or an admin API route.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.classifier import classify
from app.config import POSITIVE_CONFIDENCE_THRESHOLD
from app.dedup import deduplicate
from app.guardian_client import fetch_articles
from app.models import Article

import re

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    if not text:
        return ""
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("??", "'")
    # Replace common HTML entities manually
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")
    return text.strip()


def run_ingestion(db: Session, page_size: int = 150, query: str | None = None, region: str = "global") -> dict:
    """Runs one ingestion pass. Returns a small stats dict."""
    logger.info(">>> run_ingestion called with region=%r", region)
    if region == "bangladesh":
        from app.rss_client import fetch_rss_articles
        fetched = fetch_rss_articles()
    else:
        fetched = fetch_articles(page_size=page_size, query=query)
        
    deduped = deduplicate(fetched)

    existing_urls = {row[0] for row in db.query(Article.url).all()}
    new_articles = [a for a in deduped if a["url"] not in existing_urls]

    stored = 0
    skipped_not_positive = 0
    for article in new_articles:
        title_clean = clean_text(article["title"])
        summary_clean = clean_text(article.get("summary", ""))

        result = classify(title_clean, summary_clean)
        # For Bangladesh news, we want a slightly more relaxed classifier threshold
        # since heuristic match on Bengali keywords might be sparser, but let's stick
        # to the same threshold unless we want to dynamically adjust it.
        # Let's keep it clean: use the same threshold.
        if result.label != "positive" or result.confidence < POSITIVE_CONFIDENCE_THRESHOLD:
            skipped_not_positive += 1
            continue

        db.add(Article(
            source=article.get("source", "guardian"),
            url=article["url"],
            title=title_clean,
            summary=summary_clean,
            section=article.get("section", ""),
            image_url=article.get("image_url", ""),
            published_at=article.get("published_at"),
            label=result.label,
            confidence=result.confidence,
            score=result.score,
            region=region,
        ))
        stored += 1

    db.commit()

    stats = {
        "fetched": len(fetched),
        "after_dedup": len(deduped),
        "new": len(new_articles),
        "stored_positive": stored,
        "skipped_not_positive": skipped_not_positive,
    }
    logger.info("Ingestion run complete: %s", stats)
    return stats

