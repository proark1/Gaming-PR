from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.outlet import GamingOutlet
from app.models.scraped_article import ScrapedArticle
from app.models.scrape_job import ScrapeJob
from app.schemas.scraped_article import (
    ScrapedArticleResponse,
    ScrapedArticleListResponse,
    ScrapeJobResponse,
    ScrapeOutletResultResponse,
    ScrapeJobDetailResponse,
)
from app.services.scraper_service import scrape_all, scrape_single_outlet

router = APIRouter(prefix="/api/scraper", tags=["scraper"])


def _run_scrape_all(extract_content: bool):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        scrape_all(db, extract_content=extract_content)
    finally:
        db.close()


def _run_scrape_outlet(outlet_id: int, extract_content: bool):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        scrape_single_outlet(db, outlet_id, extract_content=extract_content)
    finally:
        db.close()


@router.post("/run", response_model=ScrapeJobResponse)
def run_all(
    background_tasks: BackgroundTasks,
    extract_content: bool = True,
    run_async: bool = False,
    db: Session = Depends(get_db),
):
    """Scrape all active outlets. Set run_async=true to run in background."""
    if run_async:
        background_tasks.add_task(_run_scrape_all, extract_content)
        return ScrapeJobResponse(
            job_id=0,
            status="queued",
            total_outlets_scraped=0,
        )
    result = scrape_all(db, extract_content=extract_content)
    return result


@router.post("/run/{outlet_id}", response_model=ScrapeOutletResultResponse)
def run_one(
    outlet_id: int,
    background_tasks: BackgroundTasks,
    extract_content: bool = True,
    run_async: bool = False,
    db: Session = Depends(get_db),
):
    """Scrape a single outlet."""
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    if run_async:
        background_tasks.add_task(_run_scrape_outlet, outlet_id, extract_content)
        return ScrapeOutletResultResponse(
            outlet_id=outlet_id,
            outlet_name=outlet.name,
            status="queued",
        )

    result = scrape_single_outlet(db, outlet_id, extract_content=extract_content)
    return result


@router.get("/jobs", response_model=list[ScrapeJobDetailResponse])
def list_jobs(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List scrape jobs."""
    query = db.query(ScrapeJob)
    if status:
        query = query.filter(ScrapeJob.status == status)
    return query.order_by(ScrapeJob.started_at.desc()).offset(skip).limit(limit).all()


@router.get("/jobs/{job_id}", response_model=ScrapeJobDetailResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return job


@router.get("/articles", response_model=list[ScrapedArticleListResponse])
def list_scraped(
    language: Optional[str] = None,
    outlet_id: Optional[int] = None,
    article_type: Optional[str] = None,
    has_full_content: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """List scraped articles with filtering."""
    query = db.query(ScrapedArticle)
    if language:
        query = query.filter(ScrapedArticle.language == language)
    if outlet_id:
        query = query.filter(ScrapedArticle.outlet_id == outlet_id)
    if article_type:
        query = query.filter(ScrapedArticle.article_type == article_type)
    if has_full_content is not None:
        query = query.filter(ScrapedArticle.is_full_content == has_full_content)
    if search:
        query = query.filter(ScrapedArticle.title.ilike(f"%{search}%"))
    return query.order_by(ScrapedArticle.scraped_at.desc()).offset(skip).limit(limit).all()


@router.get("/articles/{article_id}", response_model=ScrapedArticleResponse)
def get_scraped(article_id: int, db: Session = Depends(get_db)):
    """Get full details of a scraped article."""
    article = db.query(ScrapedArticle).filter(ScrapedArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Scraped article not found")
    return article


@router.get("/stats")
def scraper_stats(db: Session = Depends(get_db)):
    """Get scraper statistics."""
    total_articles = db.query(func.count(ScrapedArticle.id)).scalar()
    full_content = db.query(func.count(ScrapedArticle.id)).filter(ScrapedArticle.is_full_content == True).scalar()
    by_language = dict(
        db.query(ScrapedArticle.language, func.count(ScrapedArticle.id))
        .group_by(ScrapedArticle.language)
        .all()
    )
    by_type = dict(
        db.query(ScrapedArticle.article_type, func.count(ScrapedArticle.id))
        .filter(ScrapedArticle.article_type.isnot(None))
        .group_by(ScrapedArticle.article_type)
        .all()
    )
    recent_jobs = (
        db.query(ScrapeJob)
        .order_by(ScrapeJob.started_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_articles": total_articles,
        "full_content_articles": full_content,
        "articles_by_language": by_language,
        "articles_by_type": by_type,
        "recent_jobs": [
            {
                "id": j.id,
                "status": j.status,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "duration_seconds": j.duration_seconds,
                "new_articles": j.total_new_articles,
                "errors": j.total_errors,
            }
            for j in recent_jobs
        ],
    }
