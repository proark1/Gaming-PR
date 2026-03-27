import logging

from sqlalchemy.orm import Session

from app.models.outlet import GamingOutlet
from app.models.scraped_article import ScrapedArticle
from app.scrapers.base import BaseScraper
from app.scrapers.generic_rss import RssScraper
from app.scrapers.site_specific.generic_html import GenericHtmlScraper

logger = logging.getLogger(__name__)


def get_scraper(outlet: GamingOutlet) -> BaseScraper:
    if outlet.scraper_type == "rss" and outlet.rss_feed_url:
        return RssScraper(outlet)
    return GenericHtmlScraper(outlet)


def scrape_outlet(db: Session, outlet: GamingOutlet) -> dict:
    """Scrape a single outlet and return stats."""
    scraper = get_scraper(outlet)

    try:
        raw_articles = scraper.scrape()
    except Exception as e:
        logger.error(f"Scraper failed for {outlet.name}: {e}")
        return {"outlet_name": outlet.name, "articles_found": 0, "new_articles": 0, "status": f"error: {e}"}

    new_count = 0
    for article_data in raw_articles:
        url = article_data.get("url", "")
        if not url:
            continue

        existing = db.query(ScrapedArticle).filter(ScrapedArticle.url == url).first()
        if existing:
            continue

        scraped = ScrapedArticle(
            outlet_id=outlet.id,
            title=article_data["title"],
            url=url,
            summary=article_data.get("summary"),
            author=article_data.get("author"),
            published_at=article_data.get("published_at"),
            language=outlet.language,
        )
        db.add(scraped)
        new_count += 1

    db.commit()
    return {
        "outlet_name": outlet.name,
        "articles_found": len(raw_articles),
        "new_articles": new_count,
        "status": "success",
    }


def scrape_all(db: Session) -> list[dict]:
    """Scrape all active outlets."""
    outlets = db.query(GamingOutlet).filter(GamingOutlet.is_active == True).all()
    results = []
    for outlet in outlets:
        result = scrape_outlet(db, outlet)
        results.append(result)
    return results
