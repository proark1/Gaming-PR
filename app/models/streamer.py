from datetime import datetime, timezone

from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, DateTime, Float, JSON, Index

from app.database import Base


class Streamer(Base):
    """Gaming content creator — tracked across Twitch, YouTube, and X."""
    __tablename__ = "streamers"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    name = Column(String(500), nullable=False, index=True)   # Display / real name
    primary_platform = Column(String(20), nullable=False, default="twitch", index=True)
    # Platforms: twitch, youtube, x

    # Twitch
    twitch_username = Column(String(200), nullable=True, unique=True)
    twitch_channel_id = Column(String(100), nullable=True)
    twitch_url = Column(String(2048), nullable=True)
    twitch_followers = Column(Integer, nullable=True)
    twitch_avg_viewers = Column(Integer, nullable=True)
    twitch_peak_viewers = Column(Integer, nullable=True)
    twitch_is_partner = Column(Boolean, nullable=True)
    twitch_is_affiliate = Column(Boolean, nullable=True)
    twitch_description = Column(Text, nullable=True)
    twitch_profile_image_url = Column(String(2048), nullable=True)
    twitch_views_total = Column(BigInteger, nullable=True)  # channel total views

    # YouTube
    youtube_channel_id = Column(String(100), nullable=True, unique=True)
    youtube_channel_name = Column(String(500), nullable=True)
    youtube_url = Column(String(2048), nullable=True)
    youtube_subscribers = Column(Integer, nullable=True)
    youtube_total_views = Column(BigInteger, nullable=True)
    youtube_video_count = Column(Integer, nullable=True)
    youtube_avg_views_per_video = Column(Integer, nullable=True)
    youtube_description = Column(Text, nullable=True)
    youtube_profile_image_url = Column(String(2048), nullable=True)

    # X (Twitter)
    x_username = Column(String(200), nullable=True, unique=True)
    x_user_id = Column(String(100), nullable=True)
    x_url = Column(String(2048), nullable=True)
    x_followers = Column(Integer, nullable=True)
    x_following = Column(Integer, nullable=True)
    x_tweet_count = Column(Integer, nullable=True)
    x_description = Column(Text, nullable=True)
    x_profile_image_url = Column(String(2048), nullable=True)

    # Other platforms
    instagram_username = Column(String(200), nullable=True)
    instagram_url = Column(String(2048), nullable=True)
    instagram_followers = Column(Integer, nullable=True)
    tiktok_username = Column(String(200), nullable=True)
    tiktok_url = Column(String(2048), nullable=True)
    tiktok_followers = Column(Integer, nullable=True)

    # Content profile
    game_focus = Column(JSON, nullable=True, default=list)
    # e.g. ["Fortnite", "Valorant", "FPS", "RPG", "Variety"]
    content_types = Column(JSON, nullable=True, default=list)
    # e.g. ["live_streaming", "let's_play", "reviews", "tutorials", "esports"]
    language = Column(String(10), nullable=True, index=True)
    country = Column(String(100), nullable=True)
    region = Column(String(10), nullable=True)

    # Overall reach (computed / denormalized for quick sorting)
    total_followers = Column(BigInteger, nullable=True)          # sum across all platforms
    estimated_monthly_reach = Column(BigInteger, nullable=True)  # rough monthly impressions

    # PR / contact
    contact_email = Column(String(500), nullable=True)
    agent_name = Column(String(500), nullable=True)
    agent_email = Column(String(500), nullable=True)
    management_company = Column(String(500), nullable=True)
    media_kit_url = Column(String(2048), nullable=True)

    # Metadata
    profile_image_url = Column(String(2048), nullable=True)   # best available profile pic
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)              # data manually verified
    notes = Column(Text, nullable=True)

    # Freshness tracking
    last_stats_updated_at = Column(DateTime, nullable=True)
    twitch_last_live_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_streamers_language_platform", "language", "primary_platform"),
        Index("ix_streamers_total_followers", "total_followers"),
    )
