from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ScrapedArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    outlet_id: int
    title: str
    url: str
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    language: str
    scraped_at: datetime


class ScrapeResultResponse(BaseModel):
    outlet_name: str
    articles_found: int
    new_articles: int
    status: str
