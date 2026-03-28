from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import SUPPORTED_LANGUAGES
from app.database import get_db
from app.models.article import Article, ArticleTranslation
from app.schemas.article import TranslationResponse
from app.services.translation_service import translate_article
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/articles/{article_id}/translations", tags=["translations"])


@router.get("/", response_model=list[TranslationResponse])
def list_translations(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article.translations


@router.get("/languages")
def supported_languages():
    return SUPPORTED_LANGUAGES


@router.get("/{language}", response_model=TranslationResponse)
def get_translation(article_id: int, language: str, db: Session = Depends(get_db)):
    translation = (
        db.query(ArticleTranslation)
        .filter(
            ArticleTranslation.article_id == article_id,
            ArticleTranslation.language == language,
        )
        .first()
    )
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")
    return translation


@router.post("/retry", response_model=list[TranslationResponse])
def retry_translations(article_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    def _run():
        from app.database import SessionLocal
        session = SessionLocal()
        try:
            translate_article(session, article_id, retry_only=True)
        finally:
            session.close()

    background_tasks.add_task(_run)
    return article.translations
