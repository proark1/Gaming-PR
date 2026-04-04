"""Contact engagement scoring from historical outreach data."""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, UniqueConstraint, Index,
)

from app.database import Base


class ContactEngagementScore(Base):
    """
    Aggregated engagement metrics per contact computed from OutreachRecord history.
    Used by the matching engine to boost/penalize contacts based on responsiveness.
    """
    __tablename__ = "contact_engagement_scores"

    id = Column(Integer, primary_key=True, index=True)
    contact_type = Column(String(20), nullable=False)  # streamer | outlet | vc
    contact_id = Column(Integer, nullable=False)

    # Computed from OutreachRecord
    total_emails_received = Column(Integer, default=0)
    total_opens = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_replies = Column(Integer, default=0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    reply_rate = Column(Float, default=0.0)
    avg_response_time_hours = Column(Float, nullable=True)

    # Composite score: 0-100 (50 = no data / neutral)
    engagement_score = Column(Float, default=50.0)

    last_computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("contact_type", "contact_id", name="uq_engagement_contact"),
        Index("ix_engagement_score", "contact_type", "engagement_score"),
    )
