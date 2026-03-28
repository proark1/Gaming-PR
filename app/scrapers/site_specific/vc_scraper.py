"""
VC (Venture Capital) website scraper for gaming-focused investment firms.

Scrapes blog posts, portfolio news, press releases, and investment announcements
from VC firm websites. Extends the base scraper pattern with VC-specific
article discovery patterns.
"""
import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.scrapers.stealth import get_session_headers

logger = logging.getLogger(__name__)

FALLBACK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SKIP_PATTERNS = {
    "/tag/", "/category/", "/author/", "/page/",
    "/login", "/register", "/search",
    "/contact", "/privacy", "/terms", "/policy",
    "#", ".css", ".js", ".png", ".jpg", ".gif", ".svg",
    "/cdn-cgi/", "/wp-admin/", "/feed/", "/rss",
    "/careers", "/jobs", "/apply",
}

# VC-specific article URL patterns
VC_ARTICLE_PATTERNS = {
    "/blog/", "/news/", "/insights/", "/perspectives/",
    "/portfolio/", "/investments/", "/announcements/",
    "/press/", "/media/", "/updates/", "/reports/",
    "/research/", "/thought-leadership/", "/articles/",
    "/stories/", "/post/", "/publications/",
    "/2024/", "/2025/", "/2026/",
}

# Patterns for portfolio/company pages
PORTFOLIO_PATTERNS = {
    "/portfolio", "/companies", "/investments", "/our-companies",
    "/backed-companies", "/fund", "/games",
}

# Funding-related keywords for tag extraction
FUNDING_KEYWORDS = re.compile(
    r"\b(series\s*[a-e]|seed\s*round|pre-seed|funding|raised|investment|"
    r"acquisition|ipo|merger|exit|valuation|round|capital|"
    r"\$\d+[\d,.]*\s*[mb](?:illion)?)\b",
    re.IGNORECASE,
)


class VcScraper(BaseScraper):
    """Scraper for gaming-focused VC firm websites."""

    def scrape(self) -> list[dict]:
        try:
            domain = urlparse(self.outlet.url).netloc
            headers = get_session_headers(domain, language=self.outlet.language)
        except Exception:
            headers = FALLBACK_HEADERS

        config = self.outlet.scraper_config or {}
        articles = []
        seen_urls = set()

        # Scrape main page
        main_articles = self._scrape_page(self.outlet.url, headers)
        for a in main_articles:
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                articles.append(a)

        # Scrape blog/news subpages if configured or discoverable
        blog_paths = config.get("blog_paths", ["/blog", "/news", "/insights", "/perspectives"])
        for path in blog_paths:
            blog_url = urljoin(self.outlet.url, path)
            if blog_url == self.outlet.url:
                continue
            try:
                page_articles = self._scrape_page(blog_url, headers)
                for a in page_articles:
                    if a["url"] not in seen_urls:
                        seen_urls.add(a["url"])
                        articles.append(a)
            except Exception as e:
                logger.debug(f"Blog path {blog_url} failed: {e}")

        # Scrape portfolio page for company listings
        portfolio_path = config.get("portfolio_url")
        if portfolio_path:
            portfolio_url = urljoin(self.outlet.url, portfolio_path)
            try:
                portfolio_articles = self._scrape_portfolio(portfolio_url, headers)
                for a in portfolio_articles:
                    if a["url"] not in seen_urls:
                        seen_urls.add(a["url"])
                        articles.append(a)
            except Exception as e:
                logger.debug(f"Portfolio page {portfolio_url} failed: {e}")

        # Extract funding-related tags from titles/summaries
        for article in articles:
            self._extract_funding_tags(article)

        logger.info(f"Scraped {len(articles)} articles from {self.outlet.name} (VC)")
        return articles[:100]

    def _scrape_page(self, url: str, headers: dict) -> list[dict]:
        """Scrape a single page for blog posts and news articles."""
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return []

        try:
            soup = BeautifulSoup(response.text, "lxml")
        except Exception:
            soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        seen_urls = set()
        base_domain = urlparse(self.outlet.url).netloc

        # Strategy 1: Article containers
        selectors = [
            "article", ".article", ".post", ".blog-post", ".news-item",
            ".card", ".story", ".entry", ".insight", ".update",
            ".blog-card", ".post-card", ".news-card", ".content-card",
            "[class*='blog']", "[class*='post']", "[class*='news']",
        ]
        for container in soup.select(", ".join(selectors)):
            article = self._extract_from_container(container, base_domain, url)
            if article and article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                articles.append(article)

        # Strategy 2: Heading links
        for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
            link = heading.find("a", href=True)
            if not link:
                continue
            article = self._extract_from_heading_link(link, heading, base_domain, url)
            if article and article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                articles.append(article)

        # Strategy 3: All links matching VC article patterns
        if len(articles) < 5:
            for link in soup.find_all("a", href=True):
                href = link["href"]
                full_url = urljoin(url, href)
                title = link.get_text(strip=True)

                if not title or len(title) < 15 or len(title) > 300:
                    continue
                if full_url in seen_urls:
                    continue
                if not self._is_vc_article_url(full_url, base_domain):
                    continue

                seen_urls.add(full_url)
                articles.append({
                    "title": title,
                    "url": full_url,
                    "featured_image_url": self._find_nearby_image(link, url),
                })

        return articles

    def _scrape_portfolio(self, url: str, headers: dict) -> list[dict]:
        """Scrape a portfolio page for company listings as articles."""
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            return []

        try:
            soup = BeautifulSoup(response.text, "lxml")
        except Exception:
            soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        base_domain = urlparse(self.outlet.url).netloc

        # Look for company cards/items on portfolio page
        selectors = [
            ".portfolio-item", ".company-card", ".portfolio-card",
            ".company", ".investment", ".backed-company",
            "[class*='portfolio']", "[class*='company']",
        ]
        for container in soup.select(", ".join(selectors)):
            link = container.find("a", href=True)
            name_el = container.find(["h2", "h3", "h4", "h5", ".name", ".title"])
            if not name_el:
                name_el = link

            if not name_el:
                continue

            company_name = name_el.get_text(strip=True)
            if not company_name or len(company_name) < 2:
                continue

            company_url = urljoin(url, link["href"]) if link else url
            img = container.find("img", src=True)
            image_url = None
            if img:
                src = img.get("data-src") or img.get("src", "")
                if src and not src.startswith("data:"):
                    image_url = urljoin(url, src)

            desc = None
            for sel in [".description", ".summary", ".excerpt", "p"]:
                desc_el = container.select_one(sel)
                if desc_el and desc_el != name_el:
                    text = desc_el.get_text(strip=True)
                    if len(text) > 15:
                        desc = text[:500]
                        break

            articles.append({
                "title": f"Portfolio: {company_name}",
                "url": company_url,
                "summary": desc,
                "featured_image_url": image_url,
                "categories": ["portfolio"],
                "tags": ["portfolio", "gaming"],
                "article_type": "portfolio",
            })

        return articles

    def _extract_from_container(self, container, base_domain: str, page_url: str) -> dict | None:
        link = container.find("a", href=True)
        if not link:
            return None

        url = urljoin(page_url, link["href"])
        if not self._is_same_domain(url, base_domain):
            return None

        title = None
        heading = container.find(["h1", "h2", "h3", "h4"])
        if heading:
            title = heading.get_text(strip=True)
        if not title:
            title = link.get_text(strip=True)
        if not title or len(title) < 10:
            return None

        img = container.find("img", src=True)
        image_url = None
        if img:
            src = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
            if src and not src.startswith("data:"):
                image_url = urljoin(page_url, src)

        summary = None
        for sel in [".summary", ".excerpt", ".description", "p"]:
            desc = container.select_one(sel)
            if desc and desc != heading:
                text = desc.get_text(strip=True)
                if len(text) > 30:
                    summary = text[:500]
                    break

        author = None
        for sel in [".author", ".byline", "[rel='author']"]:
            el = container.select_one(sel)
            if el:
                author = el.get_text(strip=True)
                break

        published_at = None
        time_el = container.find("time", attrs={"datetime": True})
        if time_el:
            published_at = time_el["datetime"]
        if not published_at:
            date_el = container.select_one(".date, .published, [class*='date']")
            if date_el:
                published_at = date_el.get_text(strip=True)

        return {
            "title": title,
            "url": url,
            "summary": summary,
            "author": author,
            "published_at": published_at,
            "featured_image_url": image_url,
        }

    def _extract_from_heading_link(self, link, heading, base_domain: str, page_url: str) -> dict | None:
        url = urljoin(page_url, link["href"])
        if not self._is_same_domain(url, base_domain):
            return None
        if not self._is_vc_article_url(url, base_domain):
            return None

        title = heading.get_text(strip=True)
        if not title or len(title) < 12:
            return None

        return {
            "title": title,
            "url": url,
            "featured_image_url": self._find_nearby_image(heading, page_url),
        }

    def _find_nearby_image(self, element, page_url: str) -> str | None:
        parent = element.parent
        for _ in range(3):
            if parent is None:
                break
            img = parent.find("img", src=True)
            if img:
                src = img.get("data-src") or img.get("data-lazy-src") or img.get("src", "")
                if src and not src.startswith("data:"):
                    return urljoin(page_url, src)
            parent = parent.parent
        return None

    def _is_vc_article_url(self, url: str, base_domain: str) -> bool:
        if not self._is_same_domain(url, base_domain):
            return False

        url_lower = url.lower()
        for pattern in SKIP_PATTERNS:
            if pattern in url_lower:
                return False

        for pattern in VC_ARTICLE_PATTERNS:
            if pattern in url_lower:
                return True

        path = urlparse(url).path.rstrip("/")
        if path.count("/") >= 2:
            return True

        return False

    def _is_same_domain(self, url: str, base_domain: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc == "" or parsed.netloc == base_domain or parsed.netloc.endswith("." + base_domain)

    def _extract_funding_tags(self, article: dict):
        """Extract funding-related tags from article title and summary."""
        text = (article.get("title", "") + " " + (article.get("summary") or "")).lower()
        matches = FUNDING_KEYWORDS.findall(text)
        if matches:
            tags = article.get("tags", []) or []
            tags.extend([m.strip() for m in matches if m.strip()])
            article["tags"] = list(set(tags))
