from sqlalchemy.orm import Session

from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleUpdate


def create_article(db: Session, data: ArticleCreate) -> Article:
    article = Article(
        title=data.title,
        body=data.body,
        source_language=data.source_language,
        author_name=data.author_name,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_article(db: Session, article_id: int) -> Article | None:
    return db.query(Article).filter(Article.id == article_id).first()


def list_articles(db: Session, skip: int = 0, limit: int = 20) -> list[Article]:
    return db.query(Article).order_by(Article.created_at.desc()).offset(skip).limit(limit).all()


def update_article(db: Session, article_id: int, data: ArticleUpdate) -> Article | None:
    article = get_article(db, article_id)
    if not article:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)
    return article


def delete_article(db: Session, article_id: int) -> bool:
    article = get_article(db, article_id)
    if not article:
        return False
    db.delete(article)
    db.commit()
    return True
