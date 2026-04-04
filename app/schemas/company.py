"""Pydantic schemas for company/game profiles."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    genre: Optional[list[str]] = None
    platforms: Optional[list[str]] = None
    release_stage: Optional[str] = None
    target_audience: Optional[list[str]] = None
    funding_stage: Optional[str] = None
    funding_target_k: Optional[int] = None
    marketing_budget_k: Optional[int] = None
    team_size: Optional[int] = None
    revenue_model: Optional[str] = None
    preferred_streamer_tiers: Optional[list[str]] = None
    preferred_regions: Optional[list[str]] = None
    preferred_platforms: Optional[list[str]] = None
    preferred_investor_types: Optional[list[str]] = None
    trailer_url: Optional[str] = None
    pitch_deck_url: Optional[str] = None
    media_kit_url: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    genre: Optional[list[str]] = None
    platforms: Optional[list[str]] = None
    release_stage: Optional[str] = None
    target_audience: Optional[list[str]] = None
    funding_stage: Optional[str] = None
    funding_target_k: Optional[int] = None
    marketing_budget_k: Optional[int] = None
    team_size: Optional[int] = None
    revenue_model: Optional[str] = None
    preferred_streamer_tiers: Optional[list[str]] = None
    preferred_regions: Optional[list[str]] = None
    preferred_platforms: Optional[list[str]] = None
    preferred_investor_types: Optional[list[str]] = None
    trailer_url: Optional[str] = None
    pitch_deck_url: Optional[str] = None
    media_kit_url: Optional[str] = None


class CompanyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    name: str
    description: Optional[str]
    website: Optional[str]
    logo_url: Optional[str]
    genre: Optional[list]
    platforms: Optional[list]
    release_stage: Optional[str]
    target_audience: Optional[list]
    funding_stage: Optional[str]
    funding_target_k: Optional[int]
    marketing_budget_k: Optional[int]
    team_size: Optional[int]
    revenue_model: Optional[str]
    preferred_streamer_tiers: Optional[list]
    preferred_regions: Optional[list]
    preferred_platforms: Optional[list]
    preferred_investor_types: Optional[list]
    trailer_url: Optional[str]
    pitch_deck_url: Optional[str]
    media_kit_url: Optional[str]
    created_at: datetime
    updated_at: datetime
