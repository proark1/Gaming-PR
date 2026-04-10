import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import SUPPORTED_LANGUAGES, settings
from app.database import Base, engine, SessionLocal
from app.migrations import run_migrations
from app.routers import articles, outlets, scraper, translations
from app.routers.monitoring import router as monitoring_router
from app.routers.webhooks import router as webhooks_router
from app.routers.export import router as export_router
from app.routers.websocket import router as websocket_router
from app.routers.email import router as email_router
from app.routers.auth import router as auth_router
from app.routers.messages import router as messages_router
from app.routers.streamers import router as streamers_router
from app.routers.gaming_vcs import router as gaming_vcs_router
from app.routers.outreach import router as outreach_router
from app.seed.outlets import seed_outlets
from app.seed.streamers import seed_streamers
from app.seed.gaming_vcs import seed_gaming_vcs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_scrape():
    """Background scrape job triggered by APScheduler."""
    from app.services.scraper_service import scrape_all, scrape_all_adaptive
    logger.info("Starting scheduled scrape...")
    db = SessionLocal()
    try:
        if settings.ENABLE_ADAPTIVE_SCHEDULING:
            result = scrape_all_adaptive(db, extract_content=settings.FULL_CONTENT_EXTRACTION)
        else:
            result = scrape_all(db, extract_content=settings.FULL_CONTENT_EXTRACTION)
        logger.info(
            f"Scheduled scrape complete: {result['total_new_articles']} new, "
            f"{result['total_full_content_extracted']} full content, "
            f"{result['duration_seconds']}s"
        )
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")
    finally:
        db.close()


def scheduled_retry_queue():
    """Process the retry queue periodically."""
    if not settings.ENABLE_RETRY_QUEUE:
        return
    from app.services.scraper_service import process_retry_queue
    db = SessionLocal()
    try:
        result = process_retry_queue(db)
        if result["processed"] > 0:
            logger.info(f"Retry queue processed: {result}")
    except Exception as e:
        logger.error(f"Retry queue processing failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Drop stale tables + add new columns to gaming_outlets
    run_migrations(engine)
    # 2. Recreate dropped tables with the full current schema
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        outlets_added = seed_outlets(db)
        streamers_added = seed_streamers(db)
        vcs_added = seed_gaming_vcs(db)
        logger.info(
            f"Database initialized. "
            f"{outlets_added} outlets, {streamers_added} streamers, {vcs_added} gaming VCs seeded."
        )
    finally:
        db.close()

    scheduler.add_job(
        scheduled_scrape,
        "interval",
        minutes=settings.SCRAPE_INTERVAL_MINUTES,
        id="auto_scrape",
        replace_existing=True,
    )

    if settings.ENABLE_RETRY_QUEUE:
        scheduler.add_job(
            scheduled_retry_queue,
            "interval",
            minutes=5,
            id="retry_queue",
            replace_existing=True,
        )

    scheduler.start()
    logger.info(
        f"Scheduler started. Scraping every {settings.SCRAPE_INTERVAL_MINUTES} minutes. "
        f"Adaptive scheduling: {'ON' if settings.ENABLE_ADAPTIVE_SCHEDULING else 'OFF'}. "
        f"Retry queue: {'ON' if settings.ENABLE_RETRY_QUEUE else 'OFF'}."
    )

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down.")


app = FastAPI(
    title="Gaming PR Platform",
    description=(
        "The world's most advanced gaming PR platform. "
        "Manages 80+ news outlets, 25+ streamers, and 20+ gaming VCs "
        "across 10+ languages with comprehensive profile data. "
        "Features website scraping for contact enrichment, "
        "personalized outreach message generation, async news scraping, "
        "Playwright browser fallback, circuit breakers, adaptive scheduling, "
        "WebSocket live feed, webhook notifications, and bulk export."
    ),
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(messages_router)
app.include_router(articles.router)
app.include_router(translations.router)
app.include_router(outlets.router)
app.include_router(scraper.router)
app.include_router(monitoring_router)
app.include_router(webhooks_router)
app.include_router(export_router)
app.include_router(websocket_router)
app.include_router(email_router)
app.include_router(streamers_router)
app.include_router(gaming_vcs_router)
app.include_router(outreach_router)


@app.get("/", response_class=HTMLResponse)
def landing_page():
    html_path = Path(__file__).parent / "app" / "static" / "landing.html"
    return HTMLResponse(content=html_path.read_text(), status_code=200)


@app.get("/login", response_class=HTMLResponse)
def login_page():
    html_path = Path(__file__).parent / "app" / "static" / "login.html"
    return HTMLResponse(content=html_path.read_text(), status_code=200)


@app.get("/register", response_class=HTMLResponse)
def register_page():
    html_path = Path(__file__).parent / "app" / "static" / "register.html"
    return HTMLResponse(content=html_path.read_text(), status_code=200)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    html_path = Path(__file__).parent / "app" / "static" / "dashboard.html"
    return HTMLResponse(content=html_path.read_text(), status_code=200)


@app.get("/health")
def health():
    return {"status": "ok", "version": "5.0.0"}


@app.get("/api/languages")
def languages():
    return SUPPORTED_LANGUAGES


if __name__ == "__main__":
    import uvicorn
    import os
    reload = os.getenv("ENV", "production") != "production"
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=reload)
