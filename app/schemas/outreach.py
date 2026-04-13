from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GenerateMessageRequest(BaseModel):
    target_type: str  # "outlet", "streamer", "gaming_vc"
    target_id: int
    message_type: str = "pitch"  # pitch, follow_up, intro, partnership, review_request, coverage_request
    tone: str = "professional"  # professional, casual, enthusiastic, formal
    game_title: Optional[str] = None
    game_description: Optional[str] = None
    key_selling_points: Optional[list[str]] = []
    custom_context: Optional[str] = None  # Extra context to weave in


class OutreachMessageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    target_type: str
    outlet_id: Optional[int] = None
    streamer_id: Optional[int] = None
    gaming_vc_id: Optional[int] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    message_type: str
    tone: Optional[str] = None
    personalization_data: Optional[dict] = None
    game_title: Optional[str] = None
    game_description: Optional[str] = None
    key_selling_points: Optional[list] = []
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_title: Optional[str] = None
    status: str = "draft"
    sent_at: Optional[datetime] = None
    was_opened: bool = False
    was_replied: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class BulkGenerateRequest(BaseModel):
    outlet_ids: list[int]  # up to 10 at a time
    message_type: str = "pitch"
    tone: str = "professional"
    game_title: Optional[str] = None
    game_description: Optional[str] = None
    key_selling_points: Optional[list[str]] = []
    custom_context: Optional[str] = None


class OutreachStatsResponse(BaseModel):
    total_messages: int
    messages_by_type: dict[str, int]
    messages_by_target: dict[str, int]
    messages_by_status: dict[str, int]
    total_sent: int
    total_opened: int
    total_replied: int
    open_rate: float
    reply_rate: float
