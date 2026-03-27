import hashlib
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.outlet import GamingOutlet
from app.models.scraped_article import ScrapedArticle
from app.models.scrape_job import ScrapeJob
from app.scrapers.base import BaseScraper
from app.scrapers.generic_rss import RssScraper
from app.scrapers.site_specific.generic_html import GenericHtmlScraper
from app.scrapers.content_extractor import extract_full_article

logger = logging.getLogger(__name__)


def get_scraper(outlet: GamingOutlet) -> BaseScraper:
    if outlet.scraper_type == "rss" and outlet.rss_feed_url:
        return RssScraper(outlet)
    return GenericHtmlScraper(outlet)


def scrape_outlet(db: Session, outlet: GamingOutlet, extract_content: bool = True) -> dict:
    """Scrape a single outlet: discover articles, extract full content, save everything."""
    result = {
        "outlet_id": outlet.id,
        "outlet_name": outlet.name,
        "language": outlet.language,
        "articles_found": 0,
        "new_articles": 0,
        "updated_articles": 0,
        "full_content_extracted": 0,
        "errors": [],
        "status": "success",
    }

    scraper = get_scraper(outlet)

    try:
        raw_articles = scraper.scrape()
    except Exception as e:
        logger.error(f"Scraper failed for {outlet.name}: {e}")
        result["status"] = f"error: {e}"
        result["errors"].append(str(e))
        _update_outlet_failure(db, outlet)
        return result

    result["articles_found"] = len(raw_articles)

    for article_data in raw_articles:
        url = article_data.get("url", "")
        if not url:
            continue

        try:
            existing = db.query(ScrapedArticle).filter(ScrapedArticle.url == url).first()

            if existing:
                # Update existing article if we now have better data
                updated = _update_existing_article(db, existing, article_data, extract_content)
                if updated:
                    result["updated_articles"] += 1
                continue

            # New article - create it
            scraped = _create_scraped_article(outlet, article_data)
            db.add(scraped)
            db.flush()  # get ID

            # Extract full content if enabled
            if extract_content and settings.FULL_CONTENT_EXTRACTION:
                try:
                    time.sleep(settings.SCRAPE_RATE_LIMIT_DELAY)
                    full_data = extract_full_article(url, timeout=settings.SCRAPE_REQUEST_TIMEOUT)
                    _apply_full_content(scraped, full_data)
                    if scraped.is_full_content:
                        result["full_content_extracted"] += 1
                except Exception as e:
                    logger.warning(f"Content extraction failed for {url}: {e}")
                    if scraped.extraction_errors is None:
                        scraped.extraction_errors = []
                    scraped.extraction_errors.append(f"Full extraction failed: {e}")

            result["new_articles"] += 1

        except Exception as e:
            logger.error(f"Error processing article {url}: {e}")
            result["errors"].append(f"{url}: {e}")

    db.commit()
    _update_outlet_success(db, outlet, result)
    return result


def scrape_all(db: Session, extract_content: bool = True) -> dict:
    """Scrape all active outlets concurrently. Returns a ScrapeJob summary."""
    job = ScrapeJob(
        job_type="manual",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    outlets = (
        db.query(GamingOutlet)
        .filter(GamingOutlet.is_active == True)
        .order_by(GamingOutlet.priority.asc())
        .all()
    )

    all_results = []
    total_errors = []

    # Use thread pool for concurrent scraping with rate limiting
    with ThreadPoolExecutor(max_workers=settings.SCRAPE_CONCURRENCY) as executor:
        future_to_outlet = {}
        for outlet in outlets:
            future = executor.submit(_scrape_outlet_thread, outlet.id, extract_content)
            future_to_outlet[future] = outlet

        for future in as_completed(future_to_outlet):
            outlet = future_to_outlet[future]
            try:
                result = future.result(timeout=300)
                all_results.append(result)
                if result.get("errors"):
                    total_errors.extend(result["errors"])
            except Exception as e:
                logger.error(f"Thread failed for {outlet.name}: {e}")
                all_results.append({
                    "outlet_id": outlet.id,
                    "outlet_name": outlet.name,
                    "articles_found": 0,
                    "new_articles": 0,
                    "updated_articles": 0,
                    "full_content_extracted": 0,
                    "errors": [str(e)],
                    "status": "error",
                })
                total_errors.append(f"{outlet.name}: {e}")

    # Update job record
    job.status = "completed" if not total_errors else "partial"
    job.completed_at = datetime.now(timezone.utc)
    job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
    job.total_outlets_scraped = len(all_results)
    job.total_articles_found = sum(r.get("articles_found", 0) for r in all_results)
    job.total_new_articles = sum(r.get("new_articles", 0) for r in all_results)
    job.total_articles_updated = sum(r.get("updated_articles", 0) for r in all_results)
    job.total_full_content_extracted = sum(r.get("full_content_extracted", 0) for r in all_results)
    job.total_errors = len(total_errors)
    job.outlet_results = all_results
    job.errors = total_errors[:100]

    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "status": job.status,
        "duration_seconds": job.duration_seconds,
        "total_outlets_scraped": job.total_outlets_scraped,
        "total_articles_found": job.total_articles_found,
        "total_new_articles": job.total_new_articles,
        "total_articles_updated": job.total_articles_updated,
        "total_full_content_extracted": job.total_full_content_extracted,
        "total_errors": job.total_errors,
        "outlet_results": all_results,
    }


def scrape_single_outlet(db: Session, outlet_id: int, extract_content: bool = True) -> dict:
    """Scrape a single outlet with job tracking."""
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise ValueError(f"Outlet {outlet_id} not found")

    job = ScrapeJob(
        job_type="single",
        status="running",
        outlet_id=outlet.id,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()

    result = scrape_outlet(db, outlet, extract_content=extract_content)

    job.status = "completed" if result["status"] == "success" else "failed"
    job.completed_at = datetime.now(timezone.utc)
    job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
    job.total_outlets_scraped = 1
    job.total_articles_found = result["articles_found"]
    job.total_new_articles = result["new_articles"]
    job.total_articles_updated = result["updated_articles"]
    job.total_full_content_extracted = result["full_content_extracted"]
    job.total_errors = len(result["errors"])
    job.outlet_results = [result]
    job.errors = result["errors"]
    db.commit()

    result["job_id"] = job.id
    return result


def _scrape_outlet_thread(outlet_id: int, extract_content: bool) -> dict:
    """Run outlet scraping in its own DB session (for thread safety)."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
        if not outlet:
            return {"outlet_id": outlet_id, "status": "error", "errors": ["Outlet not found"]}
        return scrape_outlet(db, outlet, extract_content=extract_content)
    finally:
        db.close()


def _create_scraped_article(outlet: GamingOutlet, data: dict) -> ScrapedArticle:
    """Create a ScrapedArticle from scraped data."""
    return ScrapedArticle(
        outlet_id=outlet.id,
        title=data.get("title", "Untitled"),
        url=data["url"],
        summary=data.get("summary"),
        author=data.get("author"),
        author_url=data.get("author_url"),
        authors=data.get("authors", []),
        published_at=_parse_dt(data.get("published_at")),
        updated_at=_parse_dt(data.get("updated_at")),
        featured_image_url=data.get("featured_image_url"),
        thumbnail_url=data.get("thumbnail_url"),
        images=data.get("images", []),
        video_url=data.get("video_url"),
        videos=data.get("videos", []),
        categories=data.get("categories", []),
        tags=data.get("tags", []),
        language=outlet.language,
        raw_rss_entry=data.get("raw_rss_entry"),
    )


def _apply_full_content(article: ScrapedArticle, data: dict):
    """Apply full content extraction results onto a ScrapedArticle."""
    if data.get("full_body_text"):
        article.full_body_html = data["full_body_html"]
        article.full_body_text = data["full_body_text"]
        article.word_count = data.get("word_count")
        article.reading_time_minutes = data.get("reading_time_minutes")
        article.is_full_content = True
        article.content_extracted_at = datetime.now(timezone.utc)
        article.content_hash = data.get("content_hash")

    # Enrich with data from full extraction (only if not already set)
    if not article.summary and data.get("summary"):
        article.summary = data["summary"]
    if not article.author and data.get("author"):
        article.author = data["author"]
        article.author_url = data.get("author_url")
    if not article.authors and data.get("authors"):
        article.authors = data["authors"]
    if not article.featured_image_url and data.get("featured_image_url"):
        article.featured_image_url = data["featured_image_url"]
    if not article.thumbnail_url and data.get("thumbnail_url"):
        article.thumbnail_url = data["thumbnail_url"]
    if data.get("images"):
        article.images = data["images"]
    if data.get("videos"):
        article.videos = data["videos"]
    if not article.tags and data.get("tags"):
        article.tags = data["tags"]
    if not article.categories and data.get("categories"):
        article.categories = data["categories"]
    if not article.published_at and data.get("published_at"):
        article.published_at = _parse_dt(data["published_at"])

    # SEO metadata
    article.canonical_url = data.get("canonical_url")
    article.meta_title = data.get("meta_title")
    article.meta_description = data.get("meta_description")
    article.og_title = data.get("og_title")
    article.og_description = data.get("og_description")
    article.og_image = data.get("og_image")
    article.og_type = data.get("og_type")
    article.twitter_card = data.get("twitter_card")
    article.structured_data = data.get("structured_data")
    article.article_type = data.get("article_type")
    article.game_titles = data.get("game_titles", [])
    article.platforms = data.get("platforms", [])
    article.comment_count = data.get("comment_count")
    article.rating_score = data.get("rating_score")
    article.rating_max = data.get("rating_max")
    article.http_status_code = data.get("http_status_code")

    if data.get("extraction_errors"):
        article.extraction_errors = data["extraction_errors"]


def _update_existing_article(db: Session, existing: ScrapedArticle, new_data: dict, extract_content: bool) -> bool:
    """Update an existing article if new data is better. Returns True if updated."""
    updated = False

    # Update if we have new content we didn't have before
    if not existing.full_body_text and extract_content and settings.FULL_CONTENT_EXTRACTION:
        try:
            time.sleep(settings.SCRAPE_RATE_LIMIT_DELAY)
            full_data = extract_full_article(existing.url, timeout=settings.SCRAPE_REQUEST_TIMEOUT)
            if full_data.get("full_body_text"):
                _apply_full_content(existing, full_data)
                updated = True
        except Exception as e:
            logger.warning(f"Content extraction failed for existing article {existing.url}: {e}")

    # Update summary if we have a better one now
    if not existing.summary and new_data.get("summary"):
        existing.summary = new_data["summary"]
        updated = True

    if not existing.author and new_data.get("author"):
        existing.author = new_data["author"]
        updated = True

    if not existing.featured_image_url and new_data.get("featured_image_url"):
        existing.featured_image_url = new_data["featured_image_url"]
        updated = True

    return updated


def _update_outlet_success(db: Session, outlet: GamingOutlet, result: dict):
    """Update outlet metadata after a successful scrape."""
    now = datetime.now(timezone.utc)
    outlet.last_scraped_at = now
    outlet.last_successful_scrape_at = now
    outlet.consecutive_failures = 0
    outlet.total_articles_scraped = (outlet.total_articles_scraped or 0) + result["new_articles"]

    # Update running average
    total = outlet.total_articles_scraped or 1
    outlet.avg_articles_per_scrape = round(
        (outlet.avg_articles_per_scrape * 0.8 + result["articles_found"] * 0.2), 1
    )
    db.commit()


def _update_outlet_failure(db: Session, outlet: GamingOutlet):
    """Update outlet metadata after a failed scrape."""
    outlet.last_scraped_at = datetime.now(timezone.utc)
    outlet.consecutive_failures = (outlet.consecutive_failures or 0) + 1

    # Auto-deactivate after 10 consecutive failures
    if outlet.consecutive_failures >= 10:
        outlet.is_active = False
        logger.warning(f"Deactivated outlet {outlet.name} after {outlet.consecutive_failures} failures")

    db.commit()


def _parse_dt(val) -> datetime | None:
    """Parse a datetime value that might be a string or datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
