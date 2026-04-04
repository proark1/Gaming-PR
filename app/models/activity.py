"""Contact activity log for CRM relationship tracking."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index

from app.database import Base


class ContactActivity(Base):
    """
    Records every interaction with a contact (streamer, outlet, investor).
    Builds a full timeline for relationship management.
    """
    __tablename__ = "contact_activities"

    id = Column(Integer, primary_key=True, index=True)
    contact_type = Column(String(20), nullable=False)  # streamer / outlet / vc
    contact_id = Column(Integer, nullable=False)

    activity_type = Column(String(50), nullable=False)
    # email_sent / email_opened / email_clicked / email_bounced /
    # campaign_added / note_added / stage_changed / meeting_scheduled

    details = Column(JSON, nullable=True)  # context data
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_activity_contact", "contact_type", "contact_id"),
        Index("ix_activity_created", "created_at"),
    )
