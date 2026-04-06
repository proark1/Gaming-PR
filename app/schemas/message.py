"""Schemas for message request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.message import MessageType, MessageStatus


class MessageBase(BaseModel):
    subject: str
    body: str
    message_type: MessageType = MessageType.inquiry
    outlet_id: int


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    message_type: Optional[MessageType] = None


class MessageResponse(MessageBase):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    status: MessageStatus
    sent_via_email: bool
    sent_at: Optional[datetime] = None
    email_message_id: Optional[str] = None
    reply_count: int
    created_at: datetime
    updated_at: datetime


class MessageListResponse(BaseModel):
    """Lighter response for list endpoints."""
    model_config = {"from_attributes": True}

    id: int
    outlet_id: int
    subject: str
    message_type: MessageType
    status: MessageStatus
    sent_at: Optional[datetime] = None
    reply_count: int
    created_at: datetime
