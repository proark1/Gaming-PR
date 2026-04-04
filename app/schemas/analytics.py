"""Pydantic schemas for campaign analytics."""
from typing import Optional
from pydantic import BaseModel


class SendTimeAnalysis(BaseModel):
    best_day: Optional[str] = None  # "Monday"
    best_hour: Optional[int] = None  # 10
    hourly_rates: dict  # {hour: {opens, clicks, total}}
    daily_rates: dict   # {day: {opens, clicks, total}}


class SegmentEngagement(BaseModel):
    by_tier: dict       # {tier: {sent, opens, clicks, replies, open_rate, ...}}
    by_platform: dict   # {platform: {...}}
    by_region: dict     # {region: {...}}
    by_type: dict       # {target_type: {...}}


class FunnelStep(BaseModel):
    name: str
    count: int
    rate: float  # percentage of total
    dropoff: float  # percentage lost from previous step


class FunnelAnalysis(BaseModel):
    campaign_id: int
    campaign_name: str
    steps: list[FunnelStep]


class CampaignComparisonItem(BaseModel):
    id: int
    name: str
    total_targets: int
    sent: int
    open_rate: float
    click_rate: float
    reply_rate: float
    bounce_rate: float


class CampaignComparison(BaseModel):
    campaigns: list[CampaignComparisonItem]


class TopResponder(BaseModel):
    contact_type: str
    contact_id: int
    contact_name: str
    total_received: int
    opens: int
    clicks: int
    replies: int
    open_rate: float
    reply_rate: float


class PerformancePeriod(BaseModel):
    period: str  # "2026-W14"
    sent: int
    open_rate: float
    click_rate: float
    reply_rate: float


class PerformanceTrends(BaseModel):
    periods: list[PerformancePeriod]


class AnalyticsSummary(BaseModel):
    total_campaigns: int
    total_sent: int
    overall_open_rate: float
    overall_click_rate: float
    overall_reply_rate: float
    best_performing_campaign: Optional[str] = None
    top_responder_name: Optional[str] = None
