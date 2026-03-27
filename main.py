import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import SUPPORTED_LANGUAGES, settings
from app.database import Base, engine, SessionLocal
from app.routers import articles, outlets, scraper, translations
from app.routers.monitoring import router as monitoring_router
from app.seed.outlets import seed_outlets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_scrape():
    """Background scrape job triggered by APScheduler."""
    from app.services.scraper_service import scrape_all
    logger.info("Starting scheduled scrape...")
    db = SessionLocal()
    try:
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        added = seed_outlets(db)
        logger.info(f"Database initialized. {added} new outlets seeded.")
    finally:
        db.close()

    scheduler.add_job(
        scheduled_scrape,
        "interval",
        minutes=settings.SCRAPE_INTERVAL_MINUTES,
        id="auto_scrape",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started. Scraping every {settings.SCRAPE_INTERVAL_MINUTES} minutes.")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down.")


app = FastAPI(
    title="Gaming PR Platform",
    description="The world's best gaming news scraper. Scrapes 80+ outlets across 10 languages, "
                "extracts full article content with async concurrency, robots.txt compliance, "
                "sitemap discovery, content deduplication, and auto-translates your press releases.",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(translations.router)
app.include_router(outlets.router)
app.include_router(scraper.router)
app.include_router(monitoring_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0.0"}


@app.get("/api/languages")
def languages():
    return SUPPORTED_LANGUAGES


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
