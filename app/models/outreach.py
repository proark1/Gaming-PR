from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Target (one of these will be set)
    target_type = Column(String(50), nullable=False, index=True)  # "outlet", "streamer", "gaming_vc"
    outlet_id = Column(Integer, ForeignKey("gaming_outlets.id"), nullable=True)
    streamer_id = Column(Integer, ForeignKey("streamers.id"), nullable=True)
    gaming_vc_id = Column(Integer, ForeignKey("gaming_vcs.id"), nullable=True)

    # Message content
    subject = Column(String(1000), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    message_type = Column(String(100), nullable=False, default="pitch")  # pitch, follow_up, intro, partnership, review_request, coverage_request
    tone = Column(String(50), nullable=True, default="professional")  # professional, casual, enthusiastic, formal

    # Personalization context
    personalization_data = Column(JSON, nullable=True)  # What data points were used for personalization
    game_title = Column(String(500), nullable=True)  # Game being pitched
    game_description = Column(Text, nullable=True)
    key_selling_points = Column(JSON, nullable=True, default=list)  # ["Unique mechanic X", "Award-winning"]

    # Recipient info snapshot (at time of generation)
    recipient_name = Column(String(500), nullable=True)
    recipient_email = Column(String(500), nullable=True)
    recipient_title = Column(String(500), nullable=True)

    # Status
    status = Column(String(50), default="draft", index=True)  # draft, approved, sent, replied, bounced
    sent_at = Column(DateTime, nullable=True)
    sent_email_id = Column(Integer, nullable=True)  # Link to SentEmail if actually sent

    # Quality tracking
    was_opened = Column(Boolean, default=False)
    was_replied = Column(Boolean, default=False)
    reply_sentiment = Column(String(50), nullable=True)  # positive, neutral, negative

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    outlet = relationship("GamingOutlet", foreign_keys=[outlet_id])
    streamer = relationship("Streamer", back_populates="outreach_messages", foreign_keys=[streamer_id])
    gaming_vc = relationship("GamingVC", back_populates="outreach_messages", foreign_keys=[gaming_vc_id])
