from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum,
)
from sqlalchemy.orm import relationship

from app.database import Base


class ConnectedDomain(Base):
    """A domain connected for email sending, verified via the external email service."""
    __tablename__ = "connected_domains"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )  # pending, verifying, verified, failed
    external_domain_id = Column(String(255), nullable=True)

    # DNS records returned by the email service for user to configure
    dns_records = Column(JSON, nullable=True, default=list)

    # Metadata
    from_name_default = Column(String(255), nullable=True)
    from_email_default = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    verified_at = Column(DateTime, nullable=True)

    emails = relationship("SentEmail", back_populates="domain", cascade="all, delete-orphan")


class SentEmail(Base):
    """An email sent through the platform via the external email service."""
    __tablename__ = "sent_emails"

    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("connected_domains.id"), nullable=False, index=True)
    external_email_id = Column(String(255), nullable=True, index=True)

    # Envelope
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    to_emails = Column(JSON, nullable=False)  # list of recipient addresses
    cc = Column(JSON, nullable=True, default=list)
    bcc = Column(JSON, nullable=True, default=list)
    reply_to = Column(String(255), nullable=True)

    # Content
    subject = Column(String(1000), nullable=False)
    html_body = Column(Text, nullable=True)
    text_body = Column(Text, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="queued")  # queued, sent, delivered, bounced, failed
    error_message = Column(Text, nullable=True)

    # Tracking
    opens = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    tags = Column(JSON, nullable=True, default=list)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sent_at = Column(DateTime, nullable=True)

    domain = relationship("ConnectedDomain", back_populates="emails")
