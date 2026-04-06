"""Message model for outlet communication."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from enum import Enum as PyEnum
from app.database import Base


class MessageType(str, PyEnum):
    """Types of messages users can send to outlets."""
    inquiry = "inquiry"
    interview_request = "interview_request"
    partnership = "partnership"
    other = "other"


class MessageStatus(str, PyEnum):
    """Status of outgoing message."""
    draft = "draft"
    sent = "sent"
    failed = "failed"
    replied = "replied"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("gaming_outlets.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.inquiry)
    status = Column(Enum(MessageStatus), default=MessageStatus.draft, index=True)
    sent_via_email = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    email_message_id = Column(String(255), nullable=True)  # ID from emailservice
    reply_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
