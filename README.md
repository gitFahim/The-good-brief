# The Good Brief — MVP

A minimal positive-news aggregator: pulls articles from the Guardian API,
runs them through a heuristic classifier, keeps only stories that clear a
positivity bar, and serves them to a calm, single-page frontend.

This is intentionally scoped down to an MVP: one data source (Guardian),
one classifier (rule-based, swappable), SQLite storage, and a static
frontend with no build step.

## What's included

```
backend/
  app/
    main.py            FastAPI app + routes
    config.py           Env-based settings
    database.py          SQLAlchemy engine/session
    models.py            Article table
    schemas.py            API response shape
    guardian_client.py   Guardian API fetch + normalize
    classifier.py         Heuristic positive/neutral/negative classifier
    dedup.py               Duplicate-story detection
    ingest.py               fetch -> dedup -> classify -> filter -> store
  tests/
    test_classifier.py
    test_dedup.py
  requirements.txt
  .env.example
frontend/
  index.html            Single-file static UI (no build tooling needed)
```

## Run the backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # then add your free Guardian API key
uvicorn app.main:app --reload
```

Get a free Guardian API key at https://open-platform.theguardian.com/access/
(the placeholder key `test` in `.env.example` only returns a tiny sample
set and will rate-limit quickly).

Pull in some stories:

```bash
curl -X POST http://127.0.0.1:8000/api/admin/ingest
```

Then check what got stored:

```bash
curl http://127.0.0.1:8000/api/news
```

Note: `/api/admin/ingest` has no auth in this MVP — lock it down or move
it to a scheduled job before deploying anywhere public.

## Run the frontend

It's a static file — just open it, or serve it:

```bash
cd frontend
python3 -m http.server 5500
```

Then visit `http://127.0.0.1:5500`. It talks to the backend at
`http://127.0.0.1:8000` by default; override by setting
`window.GOOD_BRIEF_API` before the page's script runs.

## Run the tests

```bash
cd backend
pytest -q
```

10 tests cover the classifier's negation handling and the dedup logic —
the two places where "looks obviously right" and "is actually right" tend
to diverge.

## How the classifier works (and its known limits)

`classifier.py` is a hand-rolled scorer: it weighs positive/negative terms
per sentence, detects simple negation ("did not recover"), and combines a
weighted title score with the summary's sentence scores into one
confidence value. It is **not** a semantic/embedding model — it's a
heuristic that's good enough to filter a news feed and is deliberately
isolated behind one function (`classify(title, summary)`) so it can be
swapped for a real LLM call (Claude, OpenAI, etc.) later without touching
`ingest.py` or the API layer.

## What's deliberately left out of this MVP

- Only one news source (Guardian). Adding another is a new
  `*_client.py` file that returns the same normalized dict shape.
- No user accounts, saved articles, or personalization.
- No scheduled/background ingestion — trigger it manually or wire up
  a cron job / Celery beat calling `run_ingestion()`.
- No pagination beyond `limit`/`offset` on `/api/news`.
- Frontend is intentionally framework-free for a zero-build MVP; a
  Next.js rewrite is a reasonable next step once the API is stable.
