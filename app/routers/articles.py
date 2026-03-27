from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleWithTranslations,
)
from app.services.article_service import (
    create_article,
    get_article,
    list_articles,
    update_article,
    delete_article,
)
from app.services.translation_service import translate_article
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/articles", tags=["articles"])


def _run_translation(article_id: int):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        translate_article(db, article_id)
    finally:
        db.close()


@router.post("/", response_model=ArticleResponse, status_code=201)
def create(data: ArticleCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    article = create_article(db, data)
    background_tasks.add_task(_run_translation, article.id)
    return article


@router.get("/", response_model=list[ArticleResponse])
def list_all(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return list_articles(db, skip=skip, limit=limit)


@router.get("/{article_id}", response_model=ArticleWithTranslations)
def get_one(article_id: int, include_translations: bool = True, db: Session = Depends(get_db)):
    article = get_article(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not include_translations:
        article.translations = []
    return article


@router.put("/{article_id}", response_model=ArticleResponse)
def update(article_id: int, data: ArticleUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    article = update_article(db, article_id, data)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if data.title is not None or data.body is not None:
        background_tasks.add_task(_run_translation, article.id)
    return article


@router.delete("/{article_id}", status_code=204)
def delete(article_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    if not delete_article(db, article_id):
        raise HTTPException(status_code=404, detail="Article not found")
