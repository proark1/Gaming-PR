import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
import os as _os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import SUPPORTED_LANGUAGES, settings
from app.database import Base, engine, SessionLocal
from app.routers import articles, outlets, scraper, translations
from app.routers.monitoring import router as monitoring_router
from app.routers.webhooks import router as webhooks_router
from app.routers.export import router as export_router
from app.routers.websocket import router as websocket_router
from app.routers.email import router as email_router
from app.routers.auth import router as auth_router
from app.seed.outlets import seed_outlets
from app.services.auth_service import seed_admin_user

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


def _auto_migrate_columns():
    """Add missing columns to existing tables (safe for both SQLite and PostgreSQL)."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    migrations = [
        ("gaming_outlets", "contact_phone", "VARCHAR(100)"),
        ("gaming_outlets", "contact_page_url", "VARCHAR(2048)"),
        ("users", "is_admin", "BOOLEAN DEFAULT FALSE"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            if table not in inspector.get_table_names():
                continue
            existing = [c["name"] for c in inspector.get_columns(table)]
            if column not in existing:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                    conn.commit()
                    logger.info(f"Migrated: added {table}.{column}")
                except Exception as e:
                    logger.warning(f"Migration skip {table}.{column}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _auto_migrate_columns()
    db = SessionLocal()
    try:
        added = seed_outlets(db)
        logger.info(f"Database initialized. {added} new outlets seeded.")
        admin = seed_admin_user(db, email="assad.dar@gmail.com", username="assad_dar")
        if admin:
            logger.info(f"Admin user ready: {admin.email} (id={admin.id})")
    finally:
        db.close()

    from datetime import datetime, timedelta, timezone as tz
    first_scrape = datetime.now(tz.utc) + timedelta(minutes=settings.SCRAPE_INTERVAL_MINUTES)
    scheduler.add_job(
        scheduled_scrape,
        "interval",
        minutes=settings.SCRAPE_INTERVAL_MINUTES,
        id="auto_scrape",
        replace_existing=True,
        next_run_time=first_scrape,
    )

    # Retry queue runs every 5 minutes
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
        "The world's most advanced gaming news scraper. "
        "Scrapes 80+ outlets across 10 languages with async concurrency, "
        "Playwright browser fallback, stealth headers, circuit breakers, "
        "adaptive scheduling, retry queues, content change tracking, "
        "WebSocket live feed, webhook notifications, and bulk export. "
        "Includes robots.txt compliance, sitemap discovery, and content deduplication."
    ),
    version="4.0.0",
    lifespan=lifespan,
)

_cors_origins = _os.environ.get("CORS_ORIGINS", "").split(",")
_cors_origins = [o.strip() for o in _cors_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_credentials=bool(_cors_origins),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(articles.router)
app.include_router(translations.router)
app.include_router(outlets.router)
app.include_router(scraper.router)
app.include_router(monitoring_router)
app.include_router(webhooks_router)
app.include_router(export_router)
app.include_router(websocket_router)
app.include_router(email_router)
app.include_router(auth_router)

# Serve shared static assets (nav.js, etc.)
_static_dir = Path(__file__).parent / "app" / "static"
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


def _serve_page(filename: str):
    html_path = _static_dir / filename
    return HTMLResponse(content=html_path.read_text(), status_code=200)


@app.get("/", response_class=HTMLResponse)
def landing_page():
    return _serve_page("landing.html")


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    return _serve_page("dashboard.html")


@app.get("/articles", response_class=HTMLResponse)
def articles_page():
    return _serve_page("articles.html")


@app.get("/outlets", response_class=HTMLResponse)
def outlets_page():
    return _serve_page("outlets.html")


@app.get("/webhooks", response_class=HTMLResponse)
def webhooks_page():
    return _serve_page("webhooks.html")


@app.get("/export", response_class=HTMLResponse)
def export_page():
    return _serve_page("export.html")


@app.get("/emails", response_class=HTMLResponse)
def emails_page():
    return _serve_page("emails.html")


@app.get("/scraper", response_class=HTMLResponse)
def scraper_page():
    return _serve_page("scraper.html")


@app.get("/feed", response_class=HTMLResponse)
def feed_page():
    return _serve_page("feed.html")


@app.get("/manage/articles", response_class=HTMLResponse)
def manage_articles_page():
    return _serve_page("manage-articles.html")


@app.get("/translations", response_class=HTMLResponse)
def translations_page():
    return _serve_page("translations.html")


@app.get("/profile", response_class=HTMLResponse)
def profile_page():
    return _serve_page("profile.html")


@app.get("/health")
def health():
    return {"status": "ok", "version": "4.0.0"}


@app.get("/api/languages")
def languages():
    return SUPPORTED_LANGUAGES


if __name__ == "__main__":
    import uvicorn
    import os
    reload = os.getenv("ENV", "production") != "production"
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=reload)
