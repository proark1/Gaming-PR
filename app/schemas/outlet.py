from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class OutletBase(BaseModel):
    name: str
    url: str
    rss_feed_url: Optional[str] = None
    language: str
    region: str
    country: Optional[str] = None
    scraper_type: str = "rss"
    description: Optional[str] = None
    category: Optional[str] = "gaming_news"
    priority: int = 5
    social_twitter: Optional[str] = None
    social_facebook: Optional[str] = None
    social_youtube: Optional[str] = None
    contact_email: Optional[str] = None


class OutletCreate(OutletBase):
    pass


class OutletUpdate(BaseModel):
    name: Optional[str] = None
    rss_feed_url: Optional[str] = None
    is_active: Optional[bool] = None
    scraper_type: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    social_twitter: Optional[str] = None
    social_facebook: Optional[str] = None
    social_youtube: Optional[str] = None
    contact_email: Optional[str] = None
    scraper_config: Optional[dict] = None


class OutletResponse(OutletBase):
    model_config = {"from_attributes": True}

    id: int
    is_active: bool
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    monthly_visitors: Optional[int] = None

    # Editorial details
    editor_in_chief: Optional[str] = None
    editor_email: Optional[str] = None
    editorial_focus: Optional[list] = None
    content_types_accepted: Optional[list] = None
    submission_guidelines_url: Optional[str] = None
    submission_email: Optional[str] = None
    press_kit_requirements: Optional[str] = None
    typical_response_time: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    press_page_url: Optional[str] = None

    # Audience & social
    alexa_rank: Optional[int] = None
    domain_authority: Optional[int] = None
    social_twitter_followers: Optional[int] = None
    social_facebook_followers: Optional[int] = None
    social_youtube_subscribers: Optional[int] = None
    social_instagram: Optional[str] = None
    social_instagram_followers: Optional[int] = None
    social_tiktok: Optional[str] = None
    social_discord: Optional[str] = None
    newsletter_subscribers: Optional[int] = None
    podcast_name: Optional[str] = None
    podcast_url: Optional[str] = None
    youtube_channel_url: Optional[str] = None
    audience_age_range: Optional[str] = None
    audience_geography: Optional[dict] = None
    audience_platforms: Optional[list] = None

    # Coverage
    games_covered: Optional[list] = None
    platforms_covered: Optional[list] = None
    genres_covered: Optional[list] = None
    review_scale: Optional[str] = None
    publishes_reviews: Optional[bool] = None
    publishes_previews: Optional[bool] = None
    publishes_interviews: Optional[bool] = None
    publishes_features: Optional[bool] = None
    average_articles_per_day: Optional[int] = None
    staff_writers: Optional[list] = None
    freelance_opportunities: Optional[bool] = None

    # Scraping
    last_scraped_at: Optional[datetime] = None
    last_successful_scrape_at: Optional[datetime] = None
    total_articles_scraped: int = 0
    consecutive_failures: int = 0
    avg_articles_per_scrape: float = 0.0
    internal_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class OutletStatsResponse(BaseModel):
    """Aggregated stats across all outlets."""
    total_outlets: int
    active_outlets: int
    outlets_by_language: dict[str, int]
    total_articles_scraped: int
    outlets_with_failures: int
