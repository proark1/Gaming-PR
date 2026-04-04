"""Pydantic schemas for press coverage tracking."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CoverageCreate(BaseModel):
    company_id: int
    outlet_name: str
    article_url: str
    article_title: str
    outlet_id: Optional[int] = None
    coverage_type: str = "news_mention"
    sentiment: str = "neutral"
    prominence: str = "mentioned"
    excerpt: Optional[str] = None
    rating_score: Optional[float] = None
    rating_max: Optional[float] = None
    published_at: Optional[datetime] = None
    source_campaign_id: Optional[int] = None


class CoverageUpdate(BaseModel):
    coverage_type: Optional[str] = None
    sentiment: Optional[str] = None
    prominence: Optional[str] = None
    excerpt: Optional[str] = None
    rating_score: Optional[float] = None
    rating_max: Optional[float] = None
    verified: Optional[bool] = None
    source_campaign_id: Optional[int] = None


class CoverageResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    company_id: int
    outlet_id: Optional[int]
    outlet_name: str
    article_url: str
    article_title: str
    scraped_article_id: Optional[int]
    source_campaign_id: Optional[int]
    coverage_type: str
    sentiment: str
    prominence: str
    estimated_reach: Optional[int]
    estimated_media_value_usd: Optional[float]
    excerpt: Optional[str]
    rating_score: Optional[float]
    rating_max: Optional[float]
    published_at: Optional[datetime]
    discovered_at: Optional[datetime]
    verified: bool
    created_at: datetime


class CoverageSummary(BaseModel):
    total_articles: int
    total_reach: int
    total_emv: float
    by_type: dict   # {type: count}
    by_sentiment: dict  # {sentiment: count}
    by_outlet: list  # [{outlet_name, count, emv}]
