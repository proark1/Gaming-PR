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
    contact_form_url: Optional[str] = None


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
    contact_form_url: Optional[str] = None
    scraper_config: Optional[dict] = None


class OutletResponse(OutletBase):
    model_config = {"from_attributes": True}

    id: int
    is_active: bool
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    monthly_visitors: Optional[int] = None
    last_scraped_at: Optional[datetime] = None
    last_successful_scrape_at: Optional[datetime] = None
    total_articles_scraped: int = 0
    consecutive_failures: int = 0
    avg_articles_per_scrape: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None


class OutletStatsResponse(BaseModel):
    """Aggregated stats across all outlets."""
    total_outlets: int
    active_outlets: int
    outlets_by_language: dict[str, int]
    total_articles_scraped: int
    outlets_with_failures: int
