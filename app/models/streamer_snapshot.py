"""Daily streamer metric snapshots for growth tracking."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, BigInteger, Float, DateTime, ForeignKey, Index

from app.database import Base


class StreamerSnapshot(Base):
    """Point-in-time capture of a streamer's key metrics for trend analysis."""
    __tablename__ = "streamer_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    streamer_id = Column(Integer, ForeignKey("streamers.id"), nullable=False, index=True)

    total_followers = Column(BigInteger, nullable=True)
    twitch_followers = Column(Integer, nullable=True)
    youtube_subscribers = Column(Integer, nullable=True)
    kick_followers = Column(Integer, nullable=True)
    twitch_avg_viewers = Column(Integer, nullable=True)
    engagement_rate = Column(Float, nullable=True)
    influence_score = Column(Float, nullable=True)

    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("ix_snapshot_streamer_date", "streamer_id", "captured_at"),
    )
