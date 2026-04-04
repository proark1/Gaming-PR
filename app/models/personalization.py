from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class MessagePersonalization(Base):
    __tablename__ = "message_personalizations"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    target_type = Column(String(20), nullable=False)   # "outlet" | "streamer" | "vc"
    target_id = Column(Integer, nullable=False)
    target_name = Column(String(500), nullable=False)
    target_language = Column(String(10), nullable=False)
    personalized_title = Column(String, nullable=False, default="")
    personalized_body = Column(Text, nullable=False, default="")
    status = Column(String(20), nullable=False, default="pending")   # pending | completed | failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    message = relationship("Message", back_populates="personalizations")

    __table_args__ = (
        UniqueConstraint("message_id", "target_type", "target_id", name="uq_personalization"),
    )
