"""
Real-time health monitoring and scraper dashboard.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, case, text
from sqlalchemy.orm import Session

from app.config import SUPPORTED_LANGUAGES, settings
from app.database import get_db
from app.models.outlet import GamingOutlet
from app.models.scraped_article import ScrapedArticle
from app.models.scrape_job import ScrapeJob

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    """Comprehensive scraper health dashboard."""
    now = datetime.now(timezone.utc)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Batch outlet counts into a single aggregate query (was 2 separate queries)
    outlet_row = db.query(
        func.count(GamingOutlet.id).label("total"),
        func.sum(case((GamingOutlet.is_active == True, 1), else_=0)).label("active"),
    ).one()
    total_outlets = outlet_row.total or 0
    active_outlets = outlet_row.active or 0

    # Batch article counts into a single aggregate query (was 4 separate queries)
    article_row = db.query(
        func.count(ScrapedArticle.id).label("total"),
        func.sum(case((ScrapedArticle.scraped_at >= last_24h, 1), else_=0)).label("last_24h"),
        func.sum(case((ScrapedArticle.scraped_at >= last_7d, 1), else_=0)).label("last_7d"),
        func.sum(case((ScrapedArticle.is_full_content == True, 1), else_=0)).label("full_content"),
    ).one()
    total_articles = article_row.total or 0
    articles_24h = article_row.last_24h or 0
    articles_7d = article_row.last_7d or 0
    full_content_count = article_row.full_content or 0

    # Coverage by language — 3 GROUP BY queries instead of 3N individual queries
    outlet_by_lang = dict(
        db.query(GamingOutlet.language, func.count(GamingOutlet.id))
        .filter(GamingOutlet.is_active == True)
        .group_by(GamingOutlet.language)
        .all()
    )
    article_by_lang = dict(
        db.query(ScrapedArticle.language, func.count(ScrapedArticle.id))
        .group_by(ScrapedArticle.language)
        .all()
    )
    recent_by_lang = dict(
        db.query(ScrapedArticle.language, func.count(ScrapedArticle.id))
        .filter(ScrapedArticle.scraped_at >= last_24h)
        .group_by(ScrapedArticle.language)
        .all()
    )
    lang_coverage = {
        lang_code: {
            "name": lang_name,
            "active_outlets": outlet_by_lang.get(lang_code, 0),
            "total_articles": article_by_lang.get(lang_code, 0),
            "articles_24h": recent_by_lang.get(lang_code, 0),
        }
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items()
    }

    # Failing outlets
    failing_outlets = (
        db.query(GamingOutlet)
        .filter(GamingOutlet.consecutive_failures > 0)
        .order_by(GamingOutlet.consecutive_failures.desc())
        .limit(10)
        .all()
    )

    # Recent jobs
    recent_jobs = (
        db.query(ScrapeJob)
        .order_by(ScrapeJob.started_at.desc())
        .limit(10)
        .all()
    )

    # Article type distribution
    type_dist = dict(
        db.query(ScrapedArticle.article_type, func.count(ScrapedArticle.id))
        .filter(ScrapedArticle.article_type.isnot(None))
        .group_by(ScrapedArticle.article_type)
        .all()
    )

    # Top outlets by articles scraped
    top_outlets = (
        db.query(GamingOutlet)
        .filter(GamingOutlet.total_articles_scraped > 0)
        .order_by(GamingOutlet.total_articles_scraped.desc())
        .limit(15)
        .all()
    )

    # Content extraction rate
    extraction_rate = (full_content_count / total_articles * 100) if total_articles > 0 else 0

    # Category breakdown
    category_counts = dict(
        db.query(GamingOutlet.category, func.count(GamingOutlet.id))
        .filter(GamingOutlet.is_active == True)
        .group_by(GamingOutlet.category)
        .all()
    )

    return {
        "timestamp": now.isoformat(),
        "system": {
            "scrape_interval_minutes": settings.SCRAPE_INTERVAL_MINUTES,
            "concurrency": settings.SCRAPE_CONCURRENCY,
            "full_content_extraction": settings.FULL_CONTENT_EXTRACTION,
            "robots_txt_compliance": settings.RESPECT_ROBOTS_TXT,
            "sitemap_discovery": settings.ENABLE_SITEMAP_DISCOVERY,
        },
        "overview": {
            "total_outlets": total_outlets,
            "active_outlets": active_outlets,
            "inactive_outlets": total_outlets - active_outlets,
            "news_outlets": category_counts.get("gaming_news", 0),
            "vc_outlets": category_counts.get("gaming_vc", 0),
            "streamer_outlets": category_counts.get("gaming_streamer", 0),
            "total_articles": total_articles,
            "articles_last_24h": articles_24h,
            "articles_last_7d": articles_7d,
            "full_content_articles": full_content_count,
            "extraction_rate_pct": round(extraction_rate, 1),
        },
        "language_coverage": lang_coverage,
        "article_types": type_dist,
        "top_outlets": [
            {
                "id": o.id,
                "name": o.name,
                "language": o.language,
                "category": o.category,
                "total_scraped": o.total_articles_scraped,
                "avg_per_scrape": o.avg_articles_per_scrape,
                "last_scraped": o.last_scraped_at.isoformat() if o.last_scraped_at else None,
            }
            for o in top_outlets
        ],
        "failing_outlets": [
            {
                "id": o.id,
                "name": o.name,
                "language": o.language,
                "category": o.category,
                "failures": o.consecutive_failures,
                "is_active": o.is_active,
                "last_scraped": o.last_scraped_at.isoformat() if o.last_scraped_at else None,
            }
            for o in failing_outlets
        ],
        "recent_jobs": [
            {
                "id": j.id,
                "type": j.job_type,
                "status": j.status,
                "started": j.started_at.isoformat() if j.started_at else None,
                "duration_s": j.duration_seconds,
                "found": j.total_articles_found,
                "new": j.total_new_articles,
                "errors": j.total_errors,
            }
            for j in recent_jobs
        ],
    }


@router.get("/health")
def detailed_health(db: Session = Depends(get_db)):
    """Detailed health check for monitoring systems."""
    now = datetime.now(timezone.utc)
    last_hour = now - timedelta(hours=1)

    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Check if scraping is working
    recent_job = db.query(ScrapeJob).order_by(ScrapeJob.started_at.desc()).first()
    last_scrape_age = None
    if recent_job and recent_job.started_at:
        started = recent_job.started_at.replace(tzinfo=timezone.utc) if recent_job.started_at.tzinfo is None else recent_job.started_at
        last_scrape_age = (now - started).total_seconds()

    articles_last_hour = db.query(func.count(ScrapedArticle.id)).filter(
        ScrapedArticle.scraped_at >= last_hour
    ).scalar()

    failing_count = db.query(func.count(GamingOutlet.id)).filter(
        GamingOutlet.consecutive_failures >= 5
    ).scalar()

    status = "healthy"
    issues = []

    if not db_ok:
        status = "unhealthy"
        issues.append("Database connection failed")
    if last_scrape_age and last_scrape_age > settings.SCRAPE_INTERVAL_MINUTES * 60 * 2:
        status = "degraded"
        issues.append("Last scrape is overdue")
    if failing_count > 10:
        status = "degraded"
        issues.append(f"{failing_count} outlets with 5+ consecutive failures")

    return {
        "status": status,
        "timestamp": now.isoformat(),
        "database": "connected" if db_ok else "disconnected",
        "last_scrape_seconds_ago": round(last_scrape_age) if last_scrape_age else None,
        "articles_last_hour": articles_last_hour,
        "failing_outlets": failing_count,
        "issues": issues,
    }
