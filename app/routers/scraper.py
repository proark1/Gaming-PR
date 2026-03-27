from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.outlet import GamingOutlet
from app.models.scraped_article import ScrapedArticle
from app.schemas.scraped_article import ScrapedArticleResponse, ScrapeResultResponse
from app.services.scraper_service import scrape_outlet, scrape_all

router = APIRouter(prefix="/api/scraper", tags=["scraper"])


@router.post("/run", response_model=list[ScrapeResultResponse])
def run_all(db: Session = Depends(get_db)):
    """Trigger a scrape of all active outlets."""
    results = scrape_all(db)
    return results


@router.post("/run/{outlet_id}", response_model=ScrapeResultResponse)
def run_one(outlet_id: int, db: Session = Depends(get_db)):
    """Trigger a scrape for a single outlet."""
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    return scrape_outlet(db, outlet)


@router.get("/articles", response_model=list[ScrapedArticleResponse])
def list_scraped(
    language: Optional[str] = None,
    outlet_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(ScrapedArticle)
    if language:
        query = query.filter(ScrapedArticle.language == language)
    if outlet_id:
        query = query.filter(ScrapedArticle.outlet_id == outlet_id)
    return query.order_by(ScrapedArticle.scraped_at.desc()).offset(skip).limit(limit).all()


@router.get("/articles/{article_id}", response_model=ScrapedArticleResponse)
def get_scraped(article_id: int, db: Session = Depends(get_db)):
    article = db.query(ScrapedArticle).filter(ScrapedArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Scraped article not found")
    return article
