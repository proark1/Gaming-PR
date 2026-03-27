from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class OutletBase(BaseModel):
    name: str
    url: str
    rss_feed_url: Optional[str] = None
    language: str
    region: str
    scraper_type: str = "rss"


class OutletCreate(OutletBase):
    pass


class OutletUpdate(BaseModel):
    name: Optional[str] = None
    rss_feed_url: Optional[str] = None
    is_active: Optional[bool] = None
    scraper_type: Optional[str] = None


class OutletResponse(OutletBase):
    model_config = {"from_attributes": True}

    id: int
    is_active: bool
    created_at: datetime
