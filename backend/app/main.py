from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.ingest import run_ingestion
from app.models import Article
from app.schemas import ArticleOut

app = FastAPI(title="The Good Brief API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/news", response_model=list[ArticleOut])
def list_news(
    region: str = Query(default="global"),
    section: str | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Article).filter(Article.region == region)
    if section:
        q = q.filter(Article.section == section)
    q = q.order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
    return q.offset(offset).limit(limit).all()


@app.get("/api/news/{article_id}", response_model=ArticleOut)
def get_news(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@app.post("/api/admin/ingest")
def trigger_ingestion(
    region: str = Query(default="global"),
    query: str | None = None,
    db: Session = Depends(get_db)
):
    """Manually trigger an ingestion run (in production, run this from a
    scheduled job instead of exposing it publicly)."""
    return run_ingestion(db, query=query, region=region)
