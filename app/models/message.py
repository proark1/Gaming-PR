from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    source_language = Column(String, nullable=False, default="en")
    category = Column(String, nullable=False)  # gaming_news, gaming_streamer, gaming_vc
    author_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    translations = relationship("MessageTranslation", back_populates="message", cascade="all, delete-orphan")


class MessageTranslation(Base):
    __tablename__ = "message_translations"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    language = Column(String, nullable=False)
    translated_title = Column(String, nullable=False, default="")
    translated_body = Column(Text, nullable=False, default="")
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    message = relationship("Message", back_populates="translations")

    __table_args__ = (
        UniqueConstraint("message_id", "language", name="uq_message_language"),
    )
