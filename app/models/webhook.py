from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text

from app.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    url = Column(String(2048), nullable=False)
    secret = Column(String(500), nullable=True)  # HMAC signing secret
    is_active = Column(Boolean, default=True, index=True)

    # What events to notify about
    events = Column(JSON, default=list)  # ["new_article", "scrape_complete", "outlet_failed"]

    # Filters
    language_filter = Column(JSON, nullable=True)  # ["en", "ja"] or null for all
    outlet_filter = Column(JSON, nullable=True)  # [1, 2, 3] or null for all
    article_type_filter = Column(JSON, nullable=True)  # ["review", "news"] or null for all

    # Delivery tracking
    total_deliveries = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    last_delivery_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    last_response_code = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class ContentSnapshot(Base):
    """Tracks article content changes over time."""
    __tablename__ = "content_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False, index=True)
    content_hash = Column(String(64), nullable=False)
    word_count = Column(Integer, nullable=True)
    title = Column(String(1000), nullable=True)
    change_type = Column(String(50), nullable=False)  # "initial", "title_change", "content_update", "minor_edit"
    diff_summary = Column(Text, nullable=True)  # Human-readable change summary
    snapshot_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
