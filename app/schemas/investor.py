from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class InvestorBase(BaseModel):
    name: str
    short_name: Optional[str] = None
    investor_type: str = "vc"
    description: Optional[str] = None
    website: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters_city: Optional[str] = None
    headquarters_country: Optional[str] = None
    headquarters_region: Optional[str] = None
    aum_millions: Optional[float] = None
    fund_size_millions: Optional[float] = None
    typical_check_min_k: Optional[int] = None
    typical_check_max_k: Optional[int] = None
    investment_stages: Optional[list[str]] = None
    focus_areas: Optional[list[str]] = None
    active_regions: Optional[list[str]] = None
    notable_portfolio: Optional[list[dict[str, Any]]] = None
    total_known_investments: Optional[int] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    pitchbook_url: Optional[str] = None
    is_active: bool = True
    is_gaming_focused: bool = True
    notes: Optional[str] = None


class InvestorCreate(InvestorBase):
    pass


class InvestorUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    investor_type: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters_city: Optional[str] = None
    headquarters_country: Optional[str] = None
    headquarters_region: Optional[str] = None
    aum_millions: Optional[float] = None
    fund_size_millions: Optional[float] = None
    typical_check_min_k: Optional[int] = None
    typical_check_max_k: Optional[int] = None
    investment_stages: Optional[list[str]] = None
    focus_areas: Optional[list[str]] = None
    active_regions: Optional[list[str]] = None
    notable_portfolio: Optional[list[dict[str, Any]]] = None
    total_known_investments: Optional[int] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    pitchbook_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_gaming_focused: Optional[bool] = None
    notes: Optional[str] = None


class InvestorResponse(InvestorBase):
    model_config = {"from_attributes": True}

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
