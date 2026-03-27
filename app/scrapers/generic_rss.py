import logging
from datetime import datetime, timezone
from time import mktime

import feedparser

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class RssScraper(BaseScraper):
    def scrape(self) -> list[dict]:
        if not self.outlet.rss_feed_url:
            logger.warning(f"No RSS feed URL for outlet: {self.outlet.name}")
            return []

        try:
            feed = feedparser.parse(self.outlet.rss_feed_url)
        except Exception as e:
            logger.error(f"Failed to parse RSS feed for {self.outlet.name}: {e}")
            return []

        articles = []
        for entry in feed.entries:
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime.fromtimestamp(
                        mktime(entry.published_parsed), tz=timezone.utc
                    )
                except (ValueError, OverflowError):
                    pass

            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary[:1000]

            articles.append({
                "title": entry.get("title", "Untitled"),
                "url": entry.get("link", ""),
                "summary": summary,
                "author": entry.get("author", None),
                "published_at": published_at,
            })

        logger.info(f"Scraped {len(articles)} articles from {self.outlet.name}")
        return articles
