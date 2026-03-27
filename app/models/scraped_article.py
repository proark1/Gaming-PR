from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ScrapedArticle(Base):
    __tablename__ = "scraped_articles"

    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("gaming_outlets.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    summary = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    language = Column(String, nullable=False, index=True)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    outlet = relationship("GamingOutlet", back_populates="scraped_articles")
