from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False, default="guardian")
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, default="")
    section = Column(String, default="")
    image_url = Column(String, default="")
    published_at = Column(DateTime(timezone=True), nullable=True)

    label = Column(String, nullable=False, default="neutral")  # positive/neutral/negative
    confidence = Column(Float, nullable=False, default=0.0)
    score = Column(Float, nullable=False, default=0.0)
    region = Column(String, nullable=False, default="global", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
