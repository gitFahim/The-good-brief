from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    url: str
    title: str
    summary: str
    section: str
    image_url: str
    published_at: datetime | None
    label: str
    confidence: float
    score: float
    region: str
