"""Pydantic schemas for CRM activity tracking and pipeline."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ActivityResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    contact_type: str
    contact_id: int
    activity_type: str
    details: Optional[dict]
    created_by: Optional[int]
    created_at: datetime


class NoteCreate(BaseModel):
    note: str


class StageUpdate(BaseModel):
    stage: str  # new / contacted / responded / negotiating / partner / inactive


class PipelineSummary(BaseModel):
    streamers: dict  # {stage: count}
    outlets: dict
    investors: dict
