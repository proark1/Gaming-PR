import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


class GenericHtmlScraper(BaseScraper):
    """Fallback scraper that extracts article links from a site's main page."""

    def scrape(self) -> list[dict]:
        try:
            response = requests.get(self.outlet.url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {self.outlet.name} ({self.outlet.url}): {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        articles = []
        seen_urls = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(self.outlet.url, href)
            title = link.get_text(strip=True)

            if not title or len(title) < 15 or len(title) > 300:
                continue
            if full_url in seen_urls:
                continue
            if not self._looks_like_article_url(full_url):
                continue

            seen_urls.add(full_url)
            articles.append({
                "title": title,
                "url": full_url,
                "summary": None,
                "author": None,
                "published_at": None,
            })

            if len(articles) >= 30:
                break

        logger.info(f"Scraped {len(articles)} articles from {self.outlet.name} (HTML)")
        return articles

    def _looks_like_article_url(self, url: str) -> bool:
        """Heuristic check if a URL likely points to an article."""
        skip_patterns = [
            "/tag/", "/category/", "/author/", "/page/",
            "/login", "/register", "/search", "/about",
            "/contact", "/privacy", "/terms", "#",
            ".css", ".js", ".png", ".jpg", ".gif",
        ]
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False

        article_patterns = [
            "/news/", "/article/", "/review/",
            "/preview/", "/feature/", "/guide/",
            "/2024/", "/2025/", "/2026/",
        ]
        for pattern in article_patterns:
            if pattern in url.lower():
                return True

        parts = url.rstrip("/").split("/")
        if len(parts) >= 5:
            return True

        return False
