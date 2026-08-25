import os
import sys

sys.path.append(os.path.abspath("C:/Projects/Positive News Portal/the-good-brief/the-good-brief/backend"))

from app.database import SessionLocal
from app.guardian_client import fetch_articles
from app.classifier import classify
from app.ingest import clean_text

articles = fetch_articles(page_size=150)
print(f"Fetched {len(articles)} articles.")

scores = []
for a in articles:
    t = clean_text(a["title"])
    s = clean_text(a.get("summary", ""))
    res = classify(t, s)
    scores.append((res.score, res.confidence, res.label, t))

# Sort by score descending
scores.sort(key=lambda x: x[0], reverse=True)

print("\nTop 20 highest-scoring articles:")
for score, conf, label, title in scores[:20]:
    print(f"Score: {score:6.2f} | Conf: {conf:4.2f} | Label: {label:8} | Title: {title}")
