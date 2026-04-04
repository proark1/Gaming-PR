"""Press coverage tracking and earned media value computation."""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index,
)

from app.database import Base


class PressCoverage(Base):
    """
    Tracks when outlets write about the game.
    Auto-detected from scraped articles or manually entered.
    Computes estimated media value based on outlet reach.
    """
    __tablename__ = "press_coverage"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_profiles.id"), nullable=False, index=True)

    # Source
    outlet_id = Column(Integer, ForeignKey("gaming_outlets.id"), nullable=True)
    outlet_name = Column(String(500), nullable=False)
    article_url = Column(String(2048), nullable=False, unique=True)
    article_title = Column(String(1000), nullable=False)

    # Linkage
    scraped_article_id = Column(Integer, ForeignKey("scraped_articles.id"), nullable=True)
    source_campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)

    # Classification
    coverage_type = Column(String(30), nullable=False, default="news_mention")
    # review | news_mention | feature | interview | list | sponsored
    sentiment = Column(String(20), default="neutral")
    # positive | neutral | negative | mixed
    prominence = Column(String(20), default="mentioned")
    # headline | featured | mentioned | brief

    # Metrics
    estimated_reach = Column(Integer, nullable=True)  # from outlet monthly_visitors
    estimated_media_value_usd = Column(Float, nullable=True)

    # Content
    excerpt = Column(Text, nullable=True)
    rating_score = Column(Float, nullable=True)  # if review (e.g. 8.5)
    rating_max = Column(Float, nullable=True)     # (e.g. 10.0)

    published_at = Column(DateTime, nullable=True)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_coverage_company", "company_id", "published_at"),
    )
