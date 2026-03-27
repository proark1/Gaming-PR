import logging
from datetime import datetime, timezone
from time import mktime
from urllib.parse import urlparse

import feedparser
import requests

from app.scrapers.base import BaseScraper
from app.scrapers.stealth import get_session_headers

logger = logging.getLogger(__name__)

FALLBACK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


class RssScraper(BaseScraper):
    def scrape(self) -> list[dict]:
        if not self.outlet.rss_feed_url:
            logger.warning(f"No RSS feed URL for outlet: {self.outlet.name}")
            return []

        try:
            # Fetch RSS with stealth headers, then parse the content
            domain = urlparse(self.outlet.rss_feed_url).netloc
            try:
                headers = get_session_headers(domain, language=self.outlet.language)
                headers["Accept"] = "application/rss+xml, application/xml, text/xml, */*"
            except Exception:
                headers = FALLBACK_HEADERS

            resp = requests.get(self.outlet.rss_feed_url, headers=headers, timeout=20)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            logger.error(f"Failed to parse RSS feed for {self.outlet.name}: {e}")
            return []

        articles = []
        for entry in feed.entries:
            article = self._extract_entry(entry)
            if article.get("url"):
                articles.append(article)

        logger.info(f"Scraped {len(articles)} articles from {self.outlet.name} (RSS)")
        return articles

    def _extract_entry(self, entry) -> dict:
        """Extract every available field from an RSS entry."""
        published_at = self._parse_date(entry)
        updated_at = None
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                updated_at = datetime.fromtimestamp(
                    mktime(entry.updated_parsed), tz=timezone.utc
                ).isoformat()
            except (ValueError, OverflowError):
                pass

        # Summary / content
        summary = ""
        full_body_html = None
        if hasattr(entry, "content") and entry.content:
            # RSS <content:encoded> - usually the full article
            full_body_html = entry.content[0].get("value", "")
            summary = self._html_to_text(full_body_html)[:1000]
        elif hasattr(entry, "summary"):
            summary = entry.summary[:2000]

        # Media
        featured_image = None
        images = []
        videos = []

        # Media RSS (media:content, media:thumbnail)
        if hasattr(entry, "media_content"):
            for mc in entry.media_content:
                url = mc.get("url", "")
                medium = mc.get("medium", "")
                if medium == "video" or "video" in mc.get("type", ""):
                    videos.append({"url": url, "platform": "native"})
                elif url:
                    if not featured_image:
                        featured_image = url
                    images.append({
                        "url": url,
                        "width": mc.get("width"),
                        "height": mc.get("height"),
                    })

        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            for mt in entry.media_thumbnail:
                url = mt.get("url", "")
                if url and not featured_image:
                    featured_image = url

        # Enclosures (images/audio/video)
        if hasattr(entry, "enclosures"):
            for enc in entry.enclosures:
                enc_url = enc.get("href", "") or enc.get("url", "")
                enc_type = enc.get("type", "")
                if "image" in enc_type and not featured_image:
                    featured_image = enc_url
                elif "video" in enc_type:
                    videos.append({"url": enc_url, "platform": "native"})

        # Tags / categories
        tags = []
        categories = []
        if hasattr(entry, "tags"):
            for tag in entry.tags:
                term = tag.get("term", "")
                scheme = tag.get("scheme", "")
                if term:
                    if "category" in (scheme or "").lower():
                        categories.append(term)
                    else:
                        tags.append(term)

        # Authors
        author = entry.get("author")
        authors = []
        if hasattr(entry, "authors"):
            for a in entry.authors:
                name = a.get("name", "")
                if name:
                    authors.append({"name": name, "url": a.get("href")})
            if authors and not author:
                author = authors[0]["name"]

        # Store the raw entry data for debugging
        raw_entry = {}
        for key in ("title", "link", "summary", "author", "published", "updated", "id"):
            if hasattr(entry, key):
                val = getattr(entry, key)
                if isinstance(val, str):
                    raw_entry[key] = val

        return {
            "title": entry.get("title", "Untitled"),
            "url": entry.get("link", ""),
            "summary": summary,
            "full_body_html": full_body_html,
            "author": author,
            "authors": authors,
            "published_at": published_at,
            "updated_at": updated_at,
            "featured_image_url": featured_image,
            "images": images,
            "videos": videos,
            "tags": tags,
            "categories": categories,
            "raw_rss_entry": raw_entry,
        }

    def _parse_date(self, entry) -> str | None:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                return datetime.fromtimestamp(
                    mktime(entry.published_parsed), tz=timezone.utc
                ).isoformat()
            except (ValueError, OverflowError):
                pass
        return None

    def _html_to_text(self, html: str) -> str:
        from bs4 import BeautifulSoup
        try:
            return BeautifulSoup(html, "lxml").get_text(separator=" ", strip=True)
        except Exception:
            return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
