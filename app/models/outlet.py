from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class GamingOutlet(Base):
    __tablename__ = "gaming_outlets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    rss_feed_url = Column(String, nullable=True)
    language = Column(String, nullable=False, index=True)
    region = Column(String, nullable=False)
    scraper_type = Column(String, nullable=False, default="rss")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    scraped_articles = relationship("ScrapedArticle", back_populates="outlet", cascade="all, delete-orphan")
