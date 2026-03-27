import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SKIP_PATTERNS = {
    "/tag/", "/category/", "/author/", "/page/",
    "/login", "/register", "/search", "/about",
    "/contact", "/privacy", "/terms", "/policy",
    "#", ".css", ".js", ".png", ".jpg", ".gif", ".svg",
    "/cdn-cgi/", "/wp-admin/", "/feed/", "/rss",
}

ARTICLE_PATTERNS = {
    "/news/", "/article/", "/review/", "/preview/",
    "/feature/", "/guide/", "/opinion/", "/interview/",
    "/hands-on/", "/editorial/", "/analysis/",
    "/2024/", "/2025/", "/2026/",
    "/games/", "/gaming/", "/esports/",
}


class GenericHtmlScraper(BaseScraper):
    """Smart HTML scraper that discovers articles from any gaming site."""

    def scrape(self) -> list[dict]:
        try:
            response = requests.get(self.outlet.url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {self.outlet.name} ({self.outlet.url}): {e}")
            return []

        try:
            soup = BeautifulSoup(response.text, "lxml")
        except Exception:
            soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        seen_urls = set()
        base_domain = urlparse(self.outlet.url).netloc

        # Strategy 1: Find article-like containers with headings
        for container in soup.select("article, .article, .post, .news-item, .card, .story"):
            article = self._extract_from_container(container, base_domain)
            if article and article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                articles.append(article)

        # Strategy 2: Find heading links (h1-h4 with <a>)
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            link = heading.find("a", href=True)
            if not link:
                continue
            article = self._extract_from_heading_link(link, heading, base_domain)
            if article and article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                articles.append(article)

        # Strategy 3: Fallback to all links that look like articles
        if len(articles) < 5:
            for link in soup.find_all("a", href=True):
                href = link["href"]
                full_url = urljoin(self.outlet.url, href)
                title = link.get_text(strip=True)

                if not title or len(title) < 20 or len(title) > 300:
                    continue
                if full_url in seen_urls:
                    continue
                if not self._is_article_url(full_url, base_domain):
                    continue

                seen_urls.add(full_url)
                articles.append({
                    "title": title,
                    "url": full_url,
                    "featured_image_url": self._find_nearby_image(link),
                })

        logger.info(f"Scraped {len(articles)} articles from {self.outlet.name} (HTML)")
        return articles[:50]

    def _extract_from_container(self, container, base_domain: str) -> dict | None:
        """Extract article data from an article container element."""
        link = container.find("a", href=True)
        if not link:
            return None

        url = urljoin(self.outlet.url, link["href"])
        if not self._is_same_domain(url, base_domain):
            return None

        # Title: prefer heading text, fall back to link text
        title = None
        heading = container.find(["h1", "h2", "h3", "h4"])
        if heading:
            title = heading.get_text(strip=True)
        if not title:
            title = link.get_text(strip=True)
        if not title or len(title) < 10:
            return None

        # Image
        img = container.find("img", src=True)
        image_url = None
        if img:
            src = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
            if src and not src.startswith("data:"):
                image_url = urljoin(self.outlet.url, src)

        # Summary
        summary = None
        for sel in [".summary", ".excerpt", ".description", "p"]:
            desc = container.select_one(sel)
            if desc and desc != heading:
                text = desc.get_text(strip=True)
                if len(text) > 30:
                    summary = text[:500]
                    break

        # Author
        author = None
        for sel in [".author", ".byline", "[rel='author']"]:
            el = container.select_one(sel)
            if el:
                author = el.get_text(strip=True)
                break

        # Time
        published_at = None
        time_el = container.find("time", attrs={"datetime": True})
        if time_el:
            published_at = time_el["datetime"]

        return {
            "title": title,
            "url": url,
            "summary": summary,
            "author": author,
            "published_at": published_at,
            "featured_image_url": image_url,
        }

    def _extract_from_heading_link(self, link, heading, base_domain: str) -> dict | None:
        url = urljoin(self.outlet.url, link["href"])
        if not self._is_same_domain(url, base_domain):
            return None
        if not self._is_article_url(url, base_domain):
            return None

        title = heading.get_text(strip=True)
        if not title or len(title) < 15:
            return None

        return {
            "title": title,
            "url": url,
            "featured_image_url": self._find_nearby_image(heading),
        }

    def _find_nearby_image(self, element) -> str | None:
        """Look for an image near an element (sibling, parent container)."""
        parent = element.parent
        for _ in range(3):
            if parent is None:
                break
            img = parent.find("img", src=True)
            if img:
                src = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                if src and not src.startswith("data:"):
                    return urljoin(self.outlet.url, src)
            parent = parent.parent
        return None

    def _is_article_url(self, url: str, base_domain: str) -> bool:
        if not self._is_same_domain(url, base_domain):
            return False

        url_lower = url.lower()
        for pattern in SKIP_PATTERNS:
            if pattern in url_lower:
                return False

        for pattern in ARTICLE_PATTERNS:
            if pattern in url_lower:
                return True

        # Heuristic: deep paths are usually articles
        path = urlparse(url).path.rstrip("/")
        if path.count("/") >= 2:
            return True

        return False

    def _is_same_domain(self, url: str, base_domain: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc == "" or parsed.netloc == base_domain or parsed.netloc.endswith("." + base_domain)
