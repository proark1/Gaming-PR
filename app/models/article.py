from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    source_language = Column(String, nullable=False, default="en")
    author_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    translations = relationship("ArticleTranslation", back_populates="article", cascade="all, delete-orphan")


class ArticleTranslation(Base):
    __tablename__ = "article_translations"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    language = Column(String, nullable=False)
    translated_title = Column(String, nullable=False, default="")
    translated_body = Column(Text, nullable=False, default="")
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    article = relationship("Article", back_populates="translations")

    __table_args__ = (
        UniqueConstraint("article_id", "language", name="uq_article_language"),
    )
