from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ArticleBase(BaseModel):
    title: str
    body: str
    source_language: str = "en"
    author_name: Optional[str] = None


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    source_language: Optional[str] = None
    author_name: Optional[str] = None


class TranslationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    article_id: int
    language: str
    translated_title: str
    translated_body: str
    status: str
    created_at: datetime


class ArticleResponse(ArticleBase):
    model_config = {"from_attributes": True}

    id: int
    created_at: datetime
    updated_at: datetime


class ArticleWithTranslations(ArticleResponse):
    translations: list[TranslationResponse] = []
