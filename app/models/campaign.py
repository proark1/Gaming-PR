"""Campaign management and outreach tracking models."""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Campaign(Base):
    """
    An outreach campaign that groups message personalization and email sending
    into an automated pipeline targeting streamers, outlets, and/or investors.
    """
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(20), nullable=False, default="draft",
    )  # draft | personalizing | scheduled | sending | paused | completed | failed

    # Message & sending config
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    domain_id = Column(Integer, ForeignKey("connected_domains.id"), nullable=True)
    from_email = Column(String(255), nullable=True)
    from_name = Column(String(255), nullable=True)
    reply_to = Column(String(255), nullable=True)

    # Target selection
    target_types = Column(JSON, nullable=False, default=list)  # ["streamer","outlet","vc"]
    target_filters = Column(JSON, nullable=True)  # structured filter criteria
    target_ids_override = Column(JSON, nullable=True)  # explicit ID list

    # Scheduling
    send_start_at = Column(DateTime, nullable=True)
    send_window_start = Column(String(5), nullable=True)  # "09:00"
    send_window_end = Column(String(5), nullable=True)    # "17:00"
    send_window_timezone = Column(String(50), default="UTC")
    batch_size = Column(Integer, default=20)
    batch_delay_seconds = Column(Integer, default=300)

    # Follow-up config
    follow_up_enabled = Column(Boolean, default=False)
    follow_up_delay_days = Column(Integer, default=3)
    follow_up_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    max_follow_ups = Column(Integer, default=1)

    # Denormalized tracking counters
    total_targets = Column(Integer, default=0)
    personalized_count = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    bounced_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    launched_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    message = relationship("Message", foreign_keys=[message_id])
    follow_up_message = relationship("Message", foreign_keys=[follow_up_message_id])
    domain = relationship("ConnectedDomain")
    outreach_records = relationship(
        "OutreachRecord", back_populates="campaign", cascade="all, delete-orphan",
    )


class OutreachRecord(Base):
    """
    Tracks outreach to a single contact within a campaign.
    Links personalization → email sending → delivery tracking.
    """
    __tablename__ = "outreach_records"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    personalization_id = Column(
        Integer, ForeignKey("message_personalizations.id"), nullable=True,
    )
    sent_email_id = Column(Integer, ForeignKey("sent_emails.id"), nullable=True)

    # Target (denormalized for fast queries)
    target_type = Column(String(20), nullable=False)   # "streamer" | "outlet" | "vc"
    target_id = Column(Integer, nullable=False)
    target_name = Column(String(500), nullable=False)
    target_email = Column(String(500), nullable=True)

    # Status lifecycle
    status = Column(
        String(20), nullable=False, default="pending",
    )  # pending | personalizing | personalized | queued | sent |
    #    delivered | opened | clicked | replied | bounced | failed | skipped
    skip_reason = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)

    # Follow-up tracking
    follow_up_number = Column(Integer, default=0)  # 0 = initial outreach
    parent_outreach_id = Column(Integer, ForeignKey("outreach_records.id"), nullable=True)

    # Timing
    scheduled_send_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    replied_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    campaign = relationship("Campaign", back_populates="outreach_records")
    personalization = relationship("MessagePersonalization")
    sent_email = relationship("SentEmail")
    parent_outreach = relationship("OutreachRecord", remote_side="OutreachRecord.id")

    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "target_type", "target_id", "follow_up_number",
            name="uq_outreach_target",
        ),
    )


class DoNotContact(Base):
    """Bounce/unsubscribe blocklist for email outreach."""
    __tablename__ = "do_not_contact"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(500), unique=True, nullable=False, index=True)
    reason = Column(String(50), nullable=False)  # bounced | unsubscribed | manual
    source = Column(String(100), nullable=True)   # e.g. "campaign:15"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
