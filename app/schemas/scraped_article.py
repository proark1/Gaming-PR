from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class ScrapedArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    outlet_id: int
    title: str
    url: str
    canonical_url: Optional[str] = None
    summary: Optional[str] = None
    full_body_text: Optional[str] = None
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    authors: Optional[list] = None
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    featured_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    images: Optional[list] = None
    video_url: Optional[str] = None
    videos: Optional[list] = None
    language: str
    categories: Optional[list] = None
    tags: Optional[list] = None
    article_type: Optional[str] = None
    game_titles: Optional[list] = None
    platforms: Optional[list] = None
    meta_description: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    comment_count: Optional[int] = None
    rating_score: Optional[float] = None
    rating_max: Optional[float] = None
    is_full_content: bool = False
    scraped_at: datetime


class ScrapedArticleListResponse(BaseModel):
    """Lighter response for list endpoints."""
    model_config = {"from_attributes": True}

    id: int
    outlet_id: int
    title: str
    url: str
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    featured_image_url: Optional[str] = None
    language: str
    article_type: Optional[str] = None
    tags: Optional[list] = None
    platforms: Optional[list] = None
    is_full_content: bool = False
    word_count: Optional[int] = None
    scraped_at: datetime


class ScrapeOutletResultResponse(BaseModel):
    outlet_id: Optional[int] = None
    outlet_name: str = ""
    language: str = ""
    articles_found: int = 0
    new_articles: int = 0
    updated_articles: int = 0
    full_content_extracted: int = 0
    errors: list[str] = []
    status: str = ""


class ScrapeJobResponse(BaseModel):
    job_id: int
    status: str
    duration_seconds: Optional[float] = None
    total_outlets_scraped: int = 0
    total_articles_found: int = 0
    total_new_articles: int = 0
    total_articles_updated: int = 0
    total_full_content_extracted: int = 0
    total_errors: int = 0
    outlet_results: list[ScrapeOutletResultResponse] = []


class ScrapeJobDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    outlet_id: Optional[int] = None
    job_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    total_outlets_scraped: int = 0
    total_articles_found: int = 0
    total_new_articles: int = 0
    total_articles_updated: int = 0
    total_full_content_extracted: int = 0
    total_errors: int = 0
    outlet_results: Optional[list] = None
    errors: Optional[list] = None
