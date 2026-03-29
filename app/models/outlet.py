from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class GamingOutlet(Base):
    __tablename__ = "gaming_outlets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    url = Column(String(2048), unique=True, nullable=False)
    rss_feed_url = Column(String(2048), nullable=True)
    language = Column(String(10), nullable=False, index=True)
    region = Column(String(10), nullable=False)
    country = Column(String(100), nullable=True)
    scraper_type = Column(String(50), nullable=False, default="rss")
    is_active = Column(Boolean, default=True, index=True)

    # Outlet metadata
    description = Column(Text, nullable=True)
    logo_url = Column(String(2048), nullable=True)
    favicon_url = Column(String(2048), nullable=True)
    category = Column(String(100), nullable=True, default="gaming_news")
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    monthly_visitors = Column(Integer, nullable=True)
    social_twitter = Column(String(500), nullable=True)
    social_facebook = Column(String(500), nullable=True)
    social_youtube = Column(String(500), nullable=True)
    contact_email = Column(String(500), nullable=True)
    contact_form_url = Column(String(2048), nullable=True)

    # Scraping state
    last_scraped_at = Column(DateTime, nullable=True)
    last_successful_scrape_at = Column(DateTime, nullable=True)
    total_articles_scraped = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)
    avg_articles_per_scrape = Column(Float, default=0.0)

    # Flexible config per outlet
    scraper_config = Column(JSON, nullable=True, default=dict)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    scraped_articles = relationship("ScrapedArticle", back_populates="outlet", cascade="all, delete-orphan")
    scrape_jobs = relationship("ScrapeJob", back_populates="outlet", cascade="all, delete-orphan")
