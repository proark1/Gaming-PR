"""Pydantic schemas for AI pitch generation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PitchGenerateRequest(BaseModel):
    company_id: int
    target_type: str  # vc | streamer | outlet
    target_id: int
    pitch_type: str  # investment | sponsorship | press_coverage | review_key
    user_instructions: Optional[str] = None
    tone: str = "professional"  # formal | casual | enthusiastic | professional


class PitchBulkGenerateRequest(BaseModel):
    company_id: int
    target_type: str
    target_ids: list[int]
    pitch_type: str
    user_instructions: Optional[str] = None
    tone: str = "professional"


class PitchApproveRequest(BaseModel):
    edited_subject: Optional[str] = None
    edited_body: Optional[str] = None


class PitchSendRequest(BaseModel):
    pitch_ids: list[int]
    domain_id: int
    from_email: str
    from_name: str
    reply_to: Optional[str] = None


class PitchResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    company_id: int
    target_type: str
    target_id: int
    target_name: str
    pitch_type: str
    tone: str
    user_instructions: Optional[str]
    subject_line: Optional[str]
    body: Optional[str]
    claude_model_used: Optional[str]
    generation_tokens: Optional[int]
    status: str
    error_message: Optional[str]
    approved_at: Optional[datetime]
    sent_via_campaign_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
