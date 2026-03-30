from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageBase(BaseModel):
    title: str
    body: str
    source_language: str = "en"
    category: str  # gaming_news, gaming_streamer, gaming_vc
    author_name: Optional[str] = None


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    source_language: Optional[str] = None
    category: Optional[str] = None
    author_name: Optional[str] = None


class MessageTranslationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    message_id: int
    language: str
    translated_title: Optional[str] = ""
    translated_body: Optional[str] = ""
    status: str
    created_at: datetime


class MessageResponse(MessageBase):
    model_config = {"from_attributes": True}

    id: int
    created_at: datetime
    updated_at: datetime


class MessageWithTranslations(MessageResponse):
    translations: list[MessageTranslationResponse] = []
