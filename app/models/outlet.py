from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class GamingOutlet(Base):
    __tablename__ = "gaming_outlets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    url = Column(String(2048), unique=True, nullable=False)
    rss_feed_url = Column(String(2048), nullable=True)
    language = Column(String(10), nullable=False, index=True)
    region = Column(String(10), nullable=False)
    country = Column(String(100), nullable=True)
    scraper_type = Column(String(50), nullable=False, default="rss")
    is_active = Column(Boolean, default=True, index=True)

    # Outlet metadata
    description = Column(Text, nullable=True)
    logo_url = Column(String(2048), nullable=True)
    favicon_url = Column(String(2048), nullable=True)
    category = Column(String(100), nullable=True, default="gaming_news")
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    monthly_visitors = Column(Integer, nullable=True)
    social_twitter = Column(String(500), nullable=True)
    social_facebook = Column(String(500), nullable=True)
    social_youtube = Column(String(500), nullable=True)
    contact_email = Column(String(500), nullable=True)

    # Editorial details (enhanced)
    editor_in_chief = Column(String(500), nullable=True)
    editor_email = Column(String(500), nullable=True)
    editorial_focus = Column(JSON, nullable=True, default=list)  # ["reviews", "indie games", "esports", "AAA"]
    content_types_accepted = Column(JSON, nullable=True, default=list)  # ["press_release", "review_copy", "interview", "exclusive"]
    submission_guidelines_url = Column(String(2048), nullable=True)
    submission_email = Column(String(500), nullable=True)
    press_kit_requirements = Column(Text, nullable=True)
    typical_response_time = Column(String(200), nullable=True)  # "2-5 business days"
    preferred_contact_method = Column(String(100), nullable=True)  # "email", "twitter_dm", "press_form"
    press_page_url = Column(String(2048), nullable=True)

    # Audience & reach
    alexa_rank = Column(Integer, nullable=True)
    domain_authority = Column(Integer, nullable=True)  # Moz DA score
    social_twitter_followers = Column(Integer, nullable=True)
    social_facebook_followers = Column(Integer, nullable=True)
    social_youtube_subscribers = Column(Integer, nullable=True)
    social_instagram = Column(String(500), nullable=True)
    social_instagram_followers = Column(Integer, nullable=True)
    social_tiktok = Column(String(500), nullable=True)
    social_discord = Column(String(500), nullable=True)
    newsletter_subscribers = Column(Integer, nullable=True)
    podcast_name = Column(String(500), nullable=True)
    podcast_url = Column(String(2048), nullable=True)
    youtube_channel_url = Column(String(2048), nullable=True)

    # Audience demographics
    audience_age_range = Column(String(100), nullable=True)
    audience_geography = Column(JSON, nullable=True)  # {"US": 40, "UK": 15, "EU": 25}
    audience_platforms = Column(JSON, nullable=True)  # ["PC", "PlayStation", "Xbox", "Nintendo"]

    # Coverage patterns
    games_covered = Column(JSON, nullable=True, default=list)  # ["AAA", "indie", "mobile", "VR"]
    platforms_covered = Column(JSON, nullable=True, default=list)  # ["PC", "PS5", "Xbox", "Switch"]
    genres_covered = Column(JSON, nullable=True, default=list)  # ["RPG", "FPS", "Strategy", "Sports"]
    review_scale = Column(String(100), nullable=True)  # "1-10", "1-100", "letter grade", "star rating"
    publishes_reviews = Column(Boolean, nullable=True)
    publishes_previews = Column(Boolean, nullable=True)
    publishes_interviews = Column(Boolean, nullable=True)
    publishes_features = Column(Boolean, nullable=True)
    average_articles_per_day = Column(Integer, nullable=True)

    # Staff & key contacts
    staff_writers = Column(JSON, nullable=True, default=list)  # [{"name": "...", "beat": "RPG", "twitter": "..."}]
    freelance_opportunities = Column(Boolean, nullable=True)
    freelance_rate = Column(String(200), nullable=True)

    # Scraping state
    last_scraped_at = Column(DateTime, nullable=True)
    last_successful_scrape_at = Column(DateTime, nullable=True)
    total_articles_scraped = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)
    avg_articles_per_scrape = Column(Float, default=0.0)

    # Website scraped data
    scraped_data = Column(JSON, nullable=True)  # Raw scraped metadata from the outlet's site
    scrape_errors = Column(JSON, nullable=True, default=list)

    # Flexible config per outlet
    scraper_config = Column(JSON, nullable=True, default=dict)

    # Internal notes
    internal_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    scraped_articles = relationship("ScrapedArticle", back_populates="outlet", cascade="all, delete-orphan")
    scrape_jobs = relationship("ScrapeJob", back_populates="outlet", cascade="all, delete-orphan")
    outreach_messages = relationship("OutreachMessage", back_populates="outlet", cascade="all, delete-orphan",
                                     foreign_keys="OutreachMessage.outlet_id")
