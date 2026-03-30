from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessagePersonalizationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    message_id: int
    target_type: str
    target_id: int
    target_name: str
    target_language: str
    personalized_title: str
    personalized_body: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class PersonalizeRequest(BaseModel):
    target_ids: Optional[list[int]] = None  # None = all contacts
