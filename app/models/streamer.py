from datetime import datetime, timezone

from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Streamer(Base):
    __tablename__ = "streamers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    real_name = Column(String(500), nullable=True)
    url = Column(String(2048), unique=True, nullable=False)  # Primary channel URL

    # Platform presence
    platform = Column(String(50), nullable=False, default="twitch")  # twitch, youtube, kick
    twitch_username = Column(String(500), nullable=True)
    youtube_channel = Column(String(2048), nullable=True)
    youtube_channel_id = Column(String(200), nullable=True)
    kick_username = Column(String(500), nullable=True)
    tiktok_username = Column(String(500), nullable=True)

    # Profile info
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String(2048), nullable=True)
    banner_image_url = Column(String(2048), nullable=True)
    language = Column(String(10), nullable=False, default="en", index=True)
    region = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)

    # Audience & metrics
    follower_count = Column(Integer, nullable=True)
    subscriber_count = Column(Integer, nullable=True)
    avg_viewers = Column(Integer, nullable=True)
    peak_viewers = Column(Integer, nullable=True)
    total_views = Column(BigInteger, nullable=True)
    avg_stream_duration_hours = Column(Float, nullable=True)
    stream_schedule = Column(Text, nullable=True)  # e.g. "Mon-Fri 2pm-8pm EST"
    is_partnered = Column(Boolean, default=False)
    is_affiliated = Column(Boolean, default=False)

    # Content focus
    primary_game = Column(String(500), nullable=True)
    games_played = Column(JSON, nullable=True, default=list)  # ["Valorant", "Fortnite", ...]
    content_categories = Column(JSON, nullable=True, default=list)  # ["FPS", "Battle Royale", "Variety"]
    content_style = Column(String(200), nullable=True)  # "competitive", "casual", "educational", "entertainment"
    is_variety_streamer = Column(Boolean, default=False)

    # Demographics & audience info
    audience_age_range = Column(String(50), nullable=True)  # "18-34"
    audience_gender_split = Column(JSON, nullable=True)  # {"male": 70, "female": 25, "other": 5}
    audience_top_countries = Column(JSON, nullable=True)  # ["US", "UK", "CA"]

    # Social media
    social_twitter = Column(String(500), nullable=True)
    social_instagram = Column(String(500), nullable=True)
    social_discord = Column(String(500), nullable=True)
    social_tiktok = Column(String(500), nullable=True)
    social_youtube = Column(String(500), nullable=True)
    social_facebook = Column(String(500), nullable=True)
    twitter_followers = Column(Integer, nullable=True)
    instagram_followers = Column(Integer, nullable=True)
    discord_members = Column(Integer, nullable=True)

    # Contact info
    contact_email = Column(String(500), nullable=True)
    business_email = Column(String(500), nullable=True)
    manager_name = Column(String(500), nullable=True)
    manager_email = Column(String(500), nullable=True)
    agency = Column(String(500), nullable=True)
    agency_url = Column(String(2048), nullable=True)

    # Sponsorship & brand deals
    has_sponsorships = Column(Boolean, default=False)
    past_sponsors = Column(JSON, nullable=True, default=list)  # ["Red Bull", "HyperX", ...]
    estimated_sponsorship_rate = Column(String(200), nullable=True)  # "$5k-15k per stream"
    accepts_game_codes = Column(Boolean, nullable=True)
    accepts_sponsored_streams = Column(Boolean, nullable=True)
    has_merch_store = Column(Boolean, default=False)
    merch_url = Column(String(2048), nullable=True)

    # Esports
    is_esports_player = Column(Boolean, default=False)
    esports_team = Column(String(500), nullable=True)
    esports_role = Column(String(200), nullable=True)
    tournament_history = Column(JSON, nullable=True, default=list)

    # Categorization
    tier = Column(String(50), nullable=True, default="mid")  # "mega", "macro", "mid", "micro", "nano"
    category = Column(String(100), nullable=True, default="gaming")
    tags = Column(JSON, nullable=True, default=list)
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest

    # Scraping state
    is_active = Column(Boolean, default=True, index=True)
    last_scraped_at = Column(DateTime, nullable=True)
    scraped_data = Column(JSON, nullable=True)  # Raw scraped data from website
    scrape_errors = Column(JSON, nullable=True, default=list)

    # Notable achievements / talking points
    notable_achievements = Column(JSON, nullable=True, default=list)  # ["Won TwitchCon 2024", ...]
    recent_milestones = Column(JSON, nullable=True, default=list)  # ["Hit 1M followers", ...]
    content_highlights = Column(JSON, nullable=True, default=list)  # Top clips, viral moments

    # Notes
    internal_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    outreach_messages = relationship("OutreachMessage", back_populates="streamer", cascade="all, delete-orphan",
                                     foreign_keys="OutreachMessage.streamer_id")
