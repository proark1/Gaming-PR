"""Pydantic schemas for campaign management and outreach."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Target filtering
# ---------------------------------------------------------------------------

class TargetFilterSchema(BaseModel):
    """Structured filter criteria for selecting campaign targets."""
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    platforms: Optional[list[str]] = None        # ["twitch","youtube","kick"]
    languages: Optional[list[str]] = None        # ["en","es","ja"]
    countries: Optional[list[str]] = None        # ["US","UK"]
    regions: Optional[list[str]] = None          # ["NA","EU","APAC"]
    game_focus: Optional[list[str]] = None       # ["Fortnite","Valorant"]
    outlet_categories: Optional[list[str]] = None
    outlet_min_priority: Optional[int] = None
    outlet_max_priority: Optional[int] = None
    investor_types: Optional[list[str]] = None   # ["vc","angel","corporate"]
    investor_stages: Optional[list[str]] = None  # ["seed","series_a"]
    has_email: bool = True                        # only targets with email


# ---------------------------------------------------------------------------
# Campaign CRUD
# ---------------------------------------------------------------------------

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    message_id: Optional[int] = None
    domain_id: Optional[int] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    target_types: list[str] = Field(default_factory=lambda: ["streamer", "outlet"])
    target_filters: Optional[TargetFilterSchema] = None
    target_ids_override: Optional[list[int]] = None

    # Scheduling
    send_start_at: Optional[datetime] = None
    send_window_start: Optional[str] = None   # "09:00"
    send_window_end: Optional[str] = None     # "17:00"
    send_window_timezone: str = "UTC"
    batch_size: int = 20
    batch_delay_seconds: int = 300

    # Follow-up
    follow_up_enabled: bool = False
    follow_up_delay_days: int = 3
    follow_up_message_id: Optional[int] = None
    max_follow_ups: int = 1


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    message_id: Optional[int] = None
    domain_id: Optional[int] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    target_types: Optional[list[str]] = None
    target_filters: Optional[TargetFilterSchema] = None
    target_ids_override: Optional[list[int]] = None
    send_start_at: Optional[datetime] = None
    send_window_start: Optional[str] = None
    send_window_end: Optional[str] = None
    send_window_timezone: Optional[str] = None
    batch_size: Optional[int] = None
    batch_delay_seconds: Optional[int] = None
    follow_up_enabled: Optional[bool] = None
    follow_up_delay_days: Optional[int] = None
    follow_up_message_id: Optional[int] = None
    max_follow_ups: Optional[int] = None


class CampaignResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: Optional[str]
    status: str
    message_id: Optional[int]
    domain_id: Optional[int]
    from_email: Optional[str]
    from_name: Optional[str]
    reply_to: Optional[str]
    target_types: list
    target_filters: Optional[dict]
    target_ids_override: Optional[list]
    send_start_at: Optional[datetime]
    send_window_start: Optional[str]
    send_window_end: Optional[str]
    send_window_timezone: Optional[str]
    batch_size: int
    batch_delay_seconds: int
    follow_up_enabled: bool
    follow_up_delay_days: int
    follow_up_message_id: Optional[int]
    max_follow_ups: int
    total_targets: int
    personalized_count: int
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    bounced_count: int
    replied_count: int
    failed_count: int
    created_at: datetime
    updated_at: datetime
    launched_at: Optional[datetime]
    completed_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Campaign stats / preview
# ---------------------------------------------------------------------------

class CampaignPreviewResponse(BaseModel):
    total: int
    with_email: int
    without_email: int
    on_dnc_list: int
    by_type: dict  # {"streamer": 40, "outlet": 30, "vc": 10}


class CampaignStatsResponse(BaseModel):
    total_targets: int
    skipped: int
    personalized: int
    sent: int
    delivered: int
    opened: int
    clicked: int
    replied: int
    bounced: int
    failed: int
    open_rate: float
    click_rate: float
    reply_rate: float
    bounce_rate: float
    by_target_type: dict


# ---------------------------------------------------------------------------
# Outreach records
# ---------------------------------------------------------------------------

class OutreachRecordResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    campaign_id: int
    personalization_id: Optional[int]
    sent_email_id: Optional[int]
    target_type: str
    target_id: int
    target_name: str
    target_email: Optional[str]
    status: str
    skip_reason: Optional[str]
    error_message: Optional[str]
    follow_up_number: int
    parent_outreach_id: Optional[int]
    scheduled_send_at: Optional[datetime]
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    replied_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Do Not Contact
# ---------------------------------------------------------------------------

class DNCCreate(BaseModel):
    email: str
    reason: str = "manual"


class DNCResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    reason: str
    source: Optional[str]
    created_at: datetime
