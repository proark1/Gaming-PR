"""
Core scraping engine v4 - async, concurrent, with:
- Circuit breaker pattern per outlet
- Stealth headers & User-Agent rotation
- Playwright browser fallback for JS-heavy sites
- Retry queue with exponential backoff
- Content change tracking
- Webhook notifications
- WebSocket live feed broadcasting
- Adaptive scheduling
- robots.txt compliance, sitemap discovery, content dedup, ETag caching
"""
import asyncio
import logging
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from sqlalchemy.orm import Session

from app.config import settings
from app.models.outlet import GamingOutlet
from app.models.scraped_article import ScrapedArticle
from app.models.scrape_job import ScrapeJob
from app.scrapers.base import BaseScraper
from app.scrapers.generic_rss import RssScraper
from app.scrapers.site_specific.generic_html import GenericHtmlScraper
from app.scrapers.site_specific.vc_scraper import VcScraper
from app.scrapers.site_specific.streamer_scraper import StreamerScraper
from app.scrapers.content_extractor import extract_full_article
from app.scrapers.dedup import compute_simhash, is_duplicate
from app.scrapers.robots import can_fetch
from app.scrapers.sitemap import discover_sitemap_urls, parse_sitemap
from app.scrapers.circuit_breaker import circuit_breaker
from app.scrapers.retry_queue import retry_queue
from app.scrapers.stealth import reset_sessions

logger = logging.getLogger(__name__)


def get_scraper(outlet: GamingOutlet) -> BaseScraper:
    if outlet.scraper_type == "vc":
        return VcScraper(outlet)
    if outlet.scraper_type == "streamer":
        return StreamerScraper(outlet)
    if outlet.scraper_type == "rss" and outlet.rss_feed_url:
        return RssScraper(outlet)
    return GenericHtmlScraper(outlet)


# ═══════════════════════════════════════════
# Public API (sync wrappers around async)
# ═══════════════════════════════════════════


def scrape_all(db: Session, extract_content: bool = True) -> dict:
    """Scrape all active outlets concurrently."""
    reset_sessions()  # Fresh stealth headers per run
    loop = _get_or_create_event_loop()
    return loop.run_until_complete(_scrape_all_async(db, extract_content))


def scrape_all_adaptive(db: Session, extract_content: bool = True) -> dict:
    """Scrape only outlets that are due based on adaptive scheduling."""
    from app.services.adaptive_scheduler import get_outlets_due_for_scrape

    reset_sessions()
    loop = _get_or_create_event_loop()
    return loop.run_until_complete(_scrape_all_async(db, extract_content, adaptive=True))


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
    try:
        started = job.started_at.replace(tzinfo=timezone.utc) if job.started_at.tzinfo is None else job.started_at
        job.duration_seconds = (job.completed_at - started).total_seconds()
    except Exception:
        job.duration_seconds = result.get("duration_seconds", 0)
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


def process_retry_queue(db: Session) -> dict:
    """Process pending items in the retry queue."""
    if not settings.ENABLE_RETRY_QUEUE:
        return {"processed": 0}

    ready = retry_queue.get_ready_items()
    succeeded = 0
    failed = 0

    for item in ready:
        try:
            article = db.query(ScrapedArticle).filter(ScrapedArticle.id == item.article_id).first()
            if not article:
                continue

            full_data = extract_full_article(
                item.url,
                timeout=settings.SCRAPE_REQUEST_TIMEOUT,
                language=article.language,
                use_stealth=settings.ENABLE_STEALTH_HEADERS,
                use_browser_fallback=settings.ENABLE_BROWSER_FALLBACK,
            )

            if full_data.get("full_body_text"):
                _apply_full_content(article, full_data)
                db.commit()
                retry_queue.mark_success(item)
                succeeded += 1
            else:
                retry_queue.requeue(item, error="No content extracted")
                failed += 1

        except Exception as e:
            retry_queue.requeue(item, error=str(e))
            failed += 1

    return {"processed": len(ready), "succeeded": succeeded, "failed": failed}


def scrape_outlet(db: Session, outlet: GamingOutlet, extract_content: bool = True) -> dict:
    """Scrape a single outlet with all v4 features integrated."""
    import requests as _requests
    start = time.monotonic()

    result = {
        "outlet_id": outlet.id,
        "outlet_name": outlet.name,
        "language": outlet.language,
        "articles_found": 0,
        "new_articles": 0,
        "updated_articles": 0,
        "full_content_extracted": 0,
        "duplicates_skipped": 0,
        "robots_blocked": 0,
        "sitemap_articles": 0,
        "cached_responses": 0,
        "browser_rendered": 0,
        "retries_queued": 0,
        "content_changes_detected": 0,
        "errors": [],
        "status": "success",
        "duration_seconds": 0,
    }

    # Circuit breaker check
    if settings.ENABLE_CIRCUIT_BREAKER and not circuit_breaker.can_execute(outlet.id):
        result["status"] = "circuit_open"
        result["errors"].append("Circuit breaker is open - outlet temporarily blocked")
        return result

    # Phase 1: Discover articles from RSS/HTML
    scraper = get_scraper(outlet)
    try:
        raw_articles = scraper.scrape()
    except Exception as e:
        logger.error(f"Scraper failed for {outlet.name}: {e}")
        result["status"] = f"error: {e}"
        result["errors"].append(str(e))
        _update_outlet_failure(db, outlet)
        if settings.ENABLE_CIRCUIT_BREAKER:
            circuit_breaker.record_failure(outlet.id)
        return result

    # Phase 2: Discover articles from sitemaps
    if settings.ENABLE_SITEMAP_DISCOVERY:
        sitemap_articles = _discover_from_sitemaps(outlet)
        result["sitemap_articles"] = len(sitemap_articles)
        existing_urls = {a.get("url") for a in raw_articles}
        for sa in sitemap_articles:
            if sa.get("url") and sa["url"] not in existing_urls:
                raw_articles.append(sa)
                existing_urls.add(sa["url"])

    result["articles_found"] = len(raw_articles)

    # Phase 3: Pre-load data to avoid N+1 queries
    # Bulk-load existing articles for all candidate URLs (1 query instead of N)
    candidate_urls = [a.get("url", "") for a in raw_articles if a.get("url")]
    existing_map: dict[str, ScrapedArticle] = {}
    if candidate_urls:
        for art in db.query(ScrapedArticle).filter(ScrapedArticle.url.in_(candidate_urls)).all():
            existing_map[art.url] = art

    # Pre-load recent SimHashes into memory (1 query instead of N)
    recent_hashes: set[str] = set()
    if extract_content and settings.FULL_CONTENT_EXTRACTION:
        recent_hashes = {
            row[0] for row in
            db.query(ScrapedArticle.content_hash)
            .filter(ScrapedArticle.content_hash.isnot(None))
            .order_by(ScrapedArticle.scraped_at.desc())
            .limit(500)
            .all()
            if row[0]
        }

    # Phase 4: Categorize articles into new vs existing-needing-update
    new_articles_data: list[dict] = []
    existing_to_update: list[tuple[ScrapedArticle, dict]] = []
    existing_needing_content: list[ScrapedArticle] = []

    for article_data in raw_articles:
        url = article_data.get("url", "")
        if not url:
            continue
        if settings.RESPECT_ROBOTS_TXT and not can_fetch(url):
            result["robots_blocked"] += 1
            continue
        existing = existing_map.get(url)
        if existing:
            existing_to_update.append((existing, article_data))
            if not existing.full_body_text and extract_content and settings.FULL_CONTENT_EXTRACTION:
                existing_needing_content.append(existing)
        else:
            new_articles_data.append(article_data)

    # Phase 5: Extract full content in parallel for all articles needing it
    # Shared HTTP session reuses TCP connections (keep-alive) across articles from same domain
    extracted: dict[str, dict] = {}

    urls_needing_extraction = (
        [a.get("url", "") for a in new_articles_data if a.get("url")]
        + [e.url for e in existing_needing_content]
    )

    if urls_needing_extraction and extract_content and settings.FULL_CONTENT_EXTRACTION:
        http_session = _requests.Session()
        try:
            def _extract_one(url: str) -> tuple[str, dict]:
                time.sleep(settings.SCRAPE_RATE_LIMIT_DELAY)
                return url, extract_full_article(
                    url,
                    timeout=settings.SCRAPE_REQUEST_TIMEOUT,
                    language=outlet.language,
                    use_stealth=settings.ENABLE_STEALTH_HEADERS,
                    use_browser_fallback=settings.ENABLE_BROWSER_FALLBACK,
                    session=http_session,
                )

            max_workers = min(3, len(urls_needing_extraction))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for url, full_data in executor.map(_extract_one, urls_needing_extraction):
                    extracted[url] = full_data
        finally:
            http_session.close()

    # Phase 6: Process existing articles (update with pre-fetched content)
    for existing, article_data in existing_to_update:
        try:
            old_hash = existing.content_hash
            prefetched = extracted.get(existing.url)
            updated = _update_existing_article(
                db, existing, article_data, extract_content, outlet.language,
                prefetched_full_data=prefetched,
            )
            if updated:
                result["updated_articles"] += 1
                if settings.ENABLE_CHANGE_TRACKING and existing.full_body_text and old_hash:
                    try:
                        from app.services.change_tracker import track_change
                        changed = track_change(
                            db, existing, existing.full_body_text,
                            existing.title, old_hash_override=old_hash,
                        )
                        if changed:
                            result["content_changes_detected"] += 1
                    except Exception as e:
                        logger.debug(f"Change tracking error: {e}")
        except Exception as e:
            logger.error(f"Error updating article {existing.url}: {e}")
            result["errors"].append(f"{existing.url}: {e}")

    # Phase 7: Build new article objects (no DB yet)
    new_scraped: list[ScrapedArticle] = []
    retry_candidates: list[tuple[ScrapedArticle, str]] = []

    for article_data in new_articles_data:
        url = article_data.get("url", "")
        if not url:
            continue
        try:
            scraped = _create_scraped_article(outlet, article_data)
            full_data = extracted.get(url)

            if full_data:
                _apply_full_content(scraped, full_data)
                if scraped.is_full_content:
                    result["full_content_extracted"] += 1
                if full_data.get("rendered_by") == "playwright":
                    result["browser_rendered"] += 1

                # SimHash dedup against in-memory set (no DB query per article)
                if scraped.full_body_text:
                    simhash = compute_simhash(scraped.full_body_text)
                    scraped.content_hash = str(simhash)
                    if _is_near_duplicate_set(simhash, recent_hashes):
                        result["duplicates_skipped"] += 1
                        continue
                    recent_hashes.add(str(simhash))

            elif extract_content and settings.FULL_CONTENT_EXTRACTION:
                # Extraction was attempted but yielded no content
                scraped.extraction_errors = ["Content extraction failed"]
                if settings.ENABLE_RETRY_QUEUE:
                    retry_candidates.append((scraped, url))

            new_scraped.append(scraped)
            result["new_articles"] += 1

        except Exception as e:
            logger.error(f"Error processing article {url}: {e}")
            result["errors"].append(f"{url}: {e}")

    # Phase 8: Bulk save new articles + single flush (assigns IDs)
    if new_scraped:
        for s in new_scraped:
            db.add(s)
        db.flush()

    # Phase 9: Post-flush operations (change tracking, retry queue, webhooks, websocket)
    for scraped in new_scraped:
        if settings.ENABLE_CHANGE_TRACKING and scraped.full_body_text:
            try:
                from app.services.change_tracker import track_change
                track_change(db, scraped, scraped.full_body_text, scraped.title)
            except Exception:
                pass

        if settings.ENABLE_WEBHOOKS:
            try:
                from app.services.webhook_service import notify_new_article
                notify_new_article(db, {
                    "article_id": scraped.id,
                    "title": scraped.title,
                    "url": scraped.url,
                    "language": scraped.language,
                    "article_type": scraped.article_type,
                    "outlet_id": outlet.id,
                    "outlet_name": outlet.name,
                })
            except Exception as e:
                logger.debug(f"Webhook notification error: {e}")

        try:
            from app.routers.websocket import ws_manager
            if ws_manager.connection_count > 0:
                _broadcast_to_websocket(ws_manager, {
                    "article_id": scraped.id,
                    "title": scraped.title,
                    "url": scraped.url,
                    "language": scraped.language,
                    "article_type": scraped.article_type,
                    "outlet_id": outlet.id,
                    "outlet_name": outlet.name,
                    "author": scraped.author,
                    "featured_image_url": scraped.featured_image_url,
                })
        except Exception:
            pass  # WebSocket is best-effort

    for scraped, url in retry_candidates:
        if scraped.id:
            retry_queue.enqueue(scraped.id, url, outlet.id, "Content extraction failed")
            result["retries_queued"] += 1

    db.commit()
    result["duration_seconds"] = round(time.monotonic() - start, 2)
    _update_outlet_success(db, outlet, result)

    # Record circuit breaker success
    if settings.ENABLE_CIRCUIT_BREAKER:
        circuit_breaker.record_success(outlet.id)

    # Scrape contact info (always try to find more)
    try:
        from app.scrapers.contact_scraper import scrape_outlet_contact
        contact = scrape_outlet_contact(outlet.url, timeout=settings.SCRAPE_REQUEST_TIMEOUT)
        changed = False

        # Merge emails — keep existing, add new ones
        if contact.get("all_emails_found"):
            existing = set(e.strip().lower() for e in (outlet.contact_email or "").split(",") if e.strip())
            new_emails = set(e.lower() for e in contact["all_emails_found"])
            merged = existing | new_emails
            if merged and merged != existing:
                outlet.contact_email = ", ".join(sorted(merged))
                changed = True
        elif contact.get("contact_email") and not outlet.contact_email:
            outlet.contact_email = contact["contact_email"]
            changed = True

        if contact.get("contact_phone") and not outlet.contact_phone:
            outlet.contact_phone = contact["contact_phone"]
            changed = True
        if contact.get("contact_page_url") and not outlet.contact_page_url:
            outlet.contact_page_url = contact["contact_page_url"]
            changed = True

        # Update social links (only if not already set)
        social_fields = [
            "social_twitter", "social_facebook", "social_youtube",
            "social_linkedin", "social_instagram", "social_tiktok", "social_discord", "social_twitch",
        ]
        for field in social_fields:
            if contact.get(field) and not getattr(outlet, field, None):
                setattr(outlet, field, contact[field])
                changed = True

        if changed:
            db.commit()
            logger.info(f"Contact info updated for {outlet.name}: email={outlet.contact_email}, phone={outlet.contact_phone}")
    except Exception as e:
        logger.debug(f"Contact scraping failed for {outlet.name}: {e}")

    return result


# ═══════════════════════════════════════════
# Async scraping engine
# ═══════════════════════════════════════════


async def _scrape_all_async(db: Session, extract_content: bool, adaptive: bool = False) -> dict:
    """Async scrape of all active outlets with bounded concurrency."""
    job = ScrapeJob(
        job_type="adaptive" if adaptive else "manual",
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if adaptive and settings.ENABLE_ADAPTIVE_SCHEDULING:
        from app.services.adaptive_scheduler import get_outlets_due_for_scrape
        outlets = get_outlets_due_for_scrape(db)
    else:
        outlets = (
            db.query(GamingOutlet)
            .filter(GamingOutlet.is_active == True)
            .order_by(GamingOutlet.priority.asc())
            .all()
        )

    outlet_ids = [o.id for o in outlets]

    # Run outlet scraping concurrently in a thread pool
    semaphore = asyncio.Semaphore(settings.SCRAPE_CONCURRENCY)

    async def _bounded_scrape(outlet_id: int) -> dict:
        async with semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, _scrape_outlet_thread, outlet_id, extract_content
            )

    tasks = [_bounded_scrape(oid) for oid in outlet_ids]
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    outlet_results = []
    total_errors = []

    for i, result in enumerate(all_results):
        if isinstance(result, Exception):
            outlet = outlets[i] if i < len(outlets) else None
            name = outlet.name if outlet else f"outlet_{outlet_ids[i]}"
            logger.error(f"Async scrape failed for {name}: {result}")
            error_result = {
                "outlet_id": outlet_ids[i],
                "outlet_name": name,
                "articles_found": 0,
                "new_articles": 0,
                "updated_articles": 0,
                "full_content_extracted": 0,
                "errors": [str(result)],
                "status": "error",
            }
            outlet_results.append(error_result)
            total_errors.append(f"{name}: {result}")
        else:
            outlet_results.append(result)
            if result.get("errors"):
                total_errors.extend(result["errors"])

    # Update job
    job.status = "completed" if not total_errors else "partial"
    job.completed_at = datetime.now(timezone.utc)
    try:
        started = job.started_at.replace(tzinfo=timezone.utc) if job.started_at.tzinfo is None else job.started_at
        job.duration_seconds = (job.completed_at - started).total_seconds()
    except Exception:
        job.duration_seconds = 0
    job.total_outlets_scraped = len(outlet_results)
    job.total_articles_found = sum(r.get("articles_found", 0) for r in outlet_results)
    job.total_new_articles = sum(r.get("new_articles", 0) for r in outlet_results)
    job.total_articles_updated = sum(r.get("updated_articles", 0) for r in outlet_results)
    job.total_full_content_extracted = sum(r.get("full_content_extracted", 0) for r in outlet_results)
    job.total_errors = len(total_errors)
    job.outlet_results = outlet_results
    job.errors = total_errors[:100]
    db.commit()
    db.refresh(job)

    # Notify webhooks about scrape completion
    if settings.ENABLE_WEBHOOKS:
        try:
            from app.services.webhook_service import notify_scrape_complete
            notify_scrape_complete(db, {
                "job_id": job.id,
                "status": job.status,
                "duration_seconds": job.duration_seconds,
                "total_new_articles": job.total_new_articles,
                "total_outlets_scraped": job.total_outlets_scraped,
            })
        except Exception:
            pass

    # Process retry queue
    if settings.ENABLE_RETRY_QUEUE:
        try:
            retry_result = process_retry_queue(db)
            logger.info(f"Retry queue: {retry_result}")
        except Exception as e:
            logger.warning(f"Retry queue processing error: {e}")

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
        "outlet_results": outlet_results,
    }


# ═══════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════


def _broadcast_to_websocket(ws_manager, article_data: dict):
    """Safely broadcast to WebSocket from sync or async context."""
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context - schedule the coroutine
        asyncio.ensure_future(ws_manager.broadcast_article(article_data))
    except RuntimeError:
        # No running loop - create one just for this broadcast
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(ws_manager.broadcast_article(article_data))
            loop.close()
        except Exception:
            pass


def _scrape_outlet_thread(outlet_id: int, extract_content: bool) -> dict:
    """Run outlet scraping in its own DB session (thread safety)."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
        if not outlet:
            return {"outlet_id": outlet_id, "status": "error", "errors": ["Outlet not found"]}
        return scrape_outlet(db, outlet, extract_content=extract_content)
    finally:
        db.close()


def _discover_from_sitemaps(outlet: GamingOutlet) -> list[dict]:
    """Discover articles from the outlet's sitemaps."""
    try:
        config = outlet.scraper_config or {}
        sitemap_urls = config.get("sitemap_urls")

        if not sitemap_urls:
            sitemap_urls = discover_sitemap_urls(outlet.url)

        articles = []
        for sm_url in sitemap_urls[:3]:
            try:
                sm_articles = parse_sitemap(sm_url, max_age_days=3, max_urls=50)
                articles.extend(sm_articles)
            except Exception as e:
                logger.debug(f"Sitemap parse failed for {sm_url}: {e}")

        return articles[:100]

    except Exception as e:
        logger.debug(f"Sitemap discovery failed for {outlet.name}: {e}")
        return []


def _is_near_duplicate(db: Session, simhash: int, exclude_id: int) -> bool:
    """Check if a SimHash is near-duplicate of any recent article."""
    recent = (
        db.query(ScrapedArticle.content_hash)
        .filter(
            ScrapedArticle.content_hash.isnot(None),
            ScrapedArticle.id != exclude_id,
        )
        .order_by(ScrapedArticle.scraped_at.desc())
        .limit(500)
        .all()
    )

    for (existing_hash,) in recent:
        try:
            existing_simhash = int(existing_hash)
            if is_duplicate(simhash, existing_simhash):
                return True
        except (ValueError, TypeError):
            continue

    return False


def _is_near_duplicate_set(simhash: int, recent_hashes: set[str]) -> bool:
    """Check if a SimHash is near-duplicate using an in-memory set (no DB query)."""
    for existing_hash in recent_hashes:
        try:
            if is_duplicate(simhash, int(existing_hash)):
                return True
        except (ValueError, TypeError):
            continue
    return False


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


def _update_existing_article(db: Session, existing: ScrapedArticle, new_data: dict,
                              extract_content: bool, language: str = "en",
                              prefetched_full_data: dict = None) -> bool:
    """Update an existing article if new data is better."""
    updated = False

    if not existing.full_body_text and extract_content and settings.FULL_CONTENT_EXTRACTION:
        full_data = prefetched_full_data
        if full_data is None:
            # Fallback: extract synchronously if not pre-fetched
            try:
                time.sleep(settings.SCRAPE_RATE_LIMIT_DELAY)
                full_data = extract_full_article(
                    existing.url,
                    timeout=settings.SCRAPE_REQUEST_TIMEOUT,
                    language=language,
                    use_stealth=settings.ENABLE_STEALTH_HEADERS,
                    use_browser_fallback=settings.ENABLE_BROWSER_FALLBACK,
                )
            except Exception as e:
                logger.warning(f"Content extraction failed for existing article {existing.url}: {e}")
        if full_data and full_data.get("full_body_text"):
            _apply_full_content(existing, full_data)
            updated = True

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
    now = datetime.now(timezone.utc)
    outlet.last_scraped_at = now
    outlet.last_successful_scrape_at = now
    outlet.consecutive_failures = 0
    outlet.total_articles_scraped = (outlet.total_articles_scraped or 0) + result["new_articles"]
    outlet.avg_articles_per_scrape = round(
        (outlet.avg_articles_per_scrape * 0.8 + result["articles_found"] * 0.2), 1
    )
    db.commit()


def _update_outlet_failure(db: Session, outlet: GamingOutlet):
    outlet.last_scraped_at = datetime.now(timezone.utc)
    outlet.consecutive_failures = (outlet.consecutive_failures or 0) + 1
    if outlet.consecutive_failures >= 10:
        outlet.is_active = False
        logger.warning(f"Deactivated outlet {outlet.name} after {outlet.consecutive_failures} failures")

    # Notify webhooks about persistent failures
    if settings.ENABLE_WEBHOOKS and outlet.consecutive_failures >= 5:
        try:
            from app.services.webhook_service import notify_outlet_failed
            notify_outlet_failed(db, {
                "outlet_id": outlet.id,
                "outlet_name": outlet.name,
                "consecutive_failures": outlet.consecutive_failures,
                "is_active": outlet.is_active,
            })
        except Exception:
            pass

    db.commit()


def _parse_dt(val) -> datetime | None:
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


def _get_or_create_event_loop():
    """Get the current event loop or create a new one."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.new_event_loop)
                loop = future.result()
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
