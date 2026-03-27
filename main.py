import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import SUPPORTED_LANGUAGES
from app.database import Base, engine, SessionLocal
from app.routers import articles, outlets, scraper, translations
from app.seed.outlets import seed_outlets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        added = seed_outlets(db)
        logger.info(f"Database initialized. {added} new outlets seeded.")
    finally:
        db.close()
    yield


app = FastAPI(
    title="Gaming PR Platform",
    description="Scrape gaming news outlets across 10 languages, create articles, and auto-translate them.",
    version="1.0.0",
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/languages")
def languages():
    return SUPPORTED_LANGUAGES


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
