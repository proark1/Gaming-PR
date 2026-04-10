from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GamingVCBase(BaseModel):
    name: str
    url: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    firm_type: Optional[str] = "venture_capital"
    investment_stage: Optional[list] = []
    investment_focus: Optional[list] = []
    gaming_subsectors: Optional[list] = []
    thesis: Optional[str] = None
    fund_size: Optional[str] = None
    typical_check_size: Optional[str] = None
    tier: Optional[str] = "mid"
    category: Optional[str] = "gaming_vc"
    tags: Optional[list] = []
    priority: int = 5
    contact_email: Optional[str] = None
    pitch_email: Optional[str] = None
    social_twitter: Optional[str] = None
    social_linkedin: Optional[str] = None


class GamingVCCreate(GamingVCBase):
    pass


class GamingVCUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    firm_type: Optional[str] = None
    investment_stage: Optional[list] = None
    investment_focus: Optional[list] = None
    gaming_subsectors: Optional[list] = None
    thesis: Optional[str] = None
    fund_size: Optional[str] = None
    typical_check_size: Optional[str] = None
    tier: Optional[str] = None
    priority: Optional[int] = None
    contact_email: Optional[str] = None
    pitch_email: Optional[str] = None
    social_twitter: Optional[str] = None
    social_linkedin: Optional[str] = None
    tags: Optional[list] = None
    is_active: Optional[bool] = None
    internal_notes: Optional[str] = None


class GamingVCResponse(GamingVCBase):
    model_config = {"from_attributes": True}

    id: int
    is_active: bool
    logo_url: Optional[str] = None
    total_aum: Optional[str] = None
    min_check_size: Optional[str] = None
    max_check_size: Optional[str] = None
    total_investments: Optional[int] = None
    total_exits: Optional[int] = None
    notable_portfolio: Optional[list] = []
    portfolio_companies_count: Optional[int] = None
    notable_exits: Optional[list] = []
    active_portfolio_count: Optional[int] = None
    partners: Optional[list] = []
    team_size: Optional[int] = None
    key_decision_makers: Optional[list] = []
    pitch_form_url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    social_crunchbase: Optional[str] = None
    social_angellist: Optional[str] = None
    social_medium: Optional[str] = None
    twitter_followers: Optional[int] = None
    linkedin_followers: Optional[int] = None
    preferred_platforms: Optional[list] = []
    recent_investments: Optional[list] = []
    recent_news: Optional[list] = []
    blog_url: Optional[str] = None
    newsletter_url: Optional[str] = None
    podcast_url: Optional[str] = None
    events_attended: Optional[list] = []
    internal_notes: Optional[str] = None
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class GamingVCStatsResponse(BaseModel):
    total_vcs: int
    active_vcs: int
    vcs_by_type: dict[str, int]
    vcs_by_tier: dict[str, int]
    vcs_by_stage: dict[str, int]
    total_portfolio_companies: int
