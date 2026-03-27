from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Index, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class ScrapedArticle(Base):
    __tablename__ = "scraped_articles"

    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("gaming_outlets.id"), nullable=False, index=True)

    # Core article data
    title = Column(String(1000), nullable=False)
    url = Column(String(2048), unique=True, nullable=False)
    canonical_url = Column(String(2048), nullable=True)
    slug = Column(String(500), nullable=True)

    # Full content
    summary = Column(Text, nullable=True)
    full_body_html = Column(Text, nullable=True)
    full_body_text = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)
    reading_time_minutes = Column(Integer, nullable=True)

    # Authorship
    author = Column(String(500), nullable=True)
    author_url = Column(String(2048), nullable=True)
    authors = Column(JSON, nullable=True, default=list)  # [{name, url, avatar}]

    # Dates
    published_at = Column(DateTime, nullable=True, index=True)
    updated_at = Column(DateTime, nullable=True)

    # Media
    featured_image_url = Column(String(2048), nullable=True)
    thumbnail_url = Column(String(2048), nullable=True)
    images = Column(JSON, nullable=True, default=list)  # [{url, alt, width, height}]
    video_url = Column(String(2048), nullable=True)
    videos = Column(JSON, nullable=True, default=list)  # [{url, platform, embed_url}]

    # Classification
    language = Column(String(10), nullable=False, index=True)
    categories = Column(JSON, nullable=True, default=list)  # ["news", "review"]
    tags = Column(JSON, nullable=True, default=list)  # ["PS5", "RPG", "E3"]
    article_type = Column(String(100), nullable=True)  # news, review, preview, guide, opinion, interview
    game_titles = Column(JSON, nullable=True, default=list)  # games mentioned
    platforms = Column(JSON, nullable=True, default=list)  # ["PS5", "PC", "Xbox"]

    # SEO & social metadata
    meta_title = Column(String(1000), nullable=True)
    meta_description = Column(Text, nullable=True)
    og_title = Column(String(1000), nullable=True)
    og_description = Column(Text, nullable=True)
    og_image = Column(String(2048), nullable=True)
    og_type = Column(String(100), nullable=True)
    twitter_card = Column(String(100), nullable=True)

    # Structured data (JSON-LD)
    structured_data = Column(JSON, nullable=True)

    # Engagement signals (where available)
    comment_count = Column(Integer, nullable=True)
    share_count = Column(Integer, nullable=True)
    rating_score = Column(Float, nullable=True)  # for reviews
    rating_max = Column(Float, nullable=True)

    # Scrape tracking
    is_full_content = Column(Boolean, default=False)
    content_hash = Column(String(64), nullable=True)  # detect changes
    http_status_code = Column(Integer, nullable=True)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    content_extracted_at = Column(DateTime, nullable=True)
    raw_rss_entry = Column(JSON, nullable=True)  # original RSS data
    extraction_errors = Column(JSON, nullable=True, default=list)

    outlet = relationship("GamingOutlet", back_populates="scraped_articles")

    __table_args__ = (
        Index("ix_scraped_articles_outlet_published", "outlet_id", "published_at"),
        Index("ix_scraped_articles_language_scraped", "language", "scraped_at"),
    )
