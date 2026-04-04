"""Pydantic schemas for deal and sponsorship tracking."""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class DealCreate(BaseModel):
    company_id: int
    contact_type: str  # vc | streamer | outlet
    contact_id: int
    contact_name: str
    deal_type: str  # investment | sponsorship | press_partnership | review
    title: str
    description: Optional[str] = None
    deal_value_usd: Optional[float] = None
    payment_terms: Optional[str] = None
    expected_close_date: Optional[date] = None
    source_campaign_id: Optional[int] = None
    source_pitch_id: Optional[int] = None
    notes: Optional[str] = None


class DealUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deal_value_usd: Optional[float] = None
    payment_terms: Optional[str] = None
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None
    contract_url: Optional[str] = None
    pitch_deck_url: Optional[str] = None
    deliverables: Optional[list[dict]] = None
    notes: Optional[str] = None


class DealStageChange(BaseModel):
    new_stage: str
    notes: Optional[str] = None


class DealStageHistoryResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    deal_id: int
    from_stage: str
    to_stage: str
    changed_at: datetime
    notes: Optional[str]


class DealResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    company_id: int
    contact_type: str
    contact_id: int
    contact_name: str
    deal_type: str
    stage: str
    stage_changed_at: Optional[datetime]
    title: str
    description: Optional[str]
    deal_value_usd: Optional[float]
    payment_terms: Optional[str]
    contract_url: Optional[str]
    pitch_deck_url: Optional[str]
    attachments: Optional[list]
    expected_close_date: Optional[date]
    actual_close_date: Optional[date]
    source_campaign_id: Optional[int]
    source_pitch_id: Optional[int]
    deliverables: Optional[list]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class DealPipelineSummary(BaseModel):
    total_deals: int
    total_value: float
    by_stage: dict  # {stage: {count, value}}
    won_count: int
    lost_count: int
    win_rate: float
