"""
Sitemap discovery and parsing.

Finds articles via XML sitemaps (sitemap.xml, sitemap_index.xml, news sitemaps)
which are often more complete than RSS feeds or homepage scraping.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "GamingPRBot/2.0",
    "Accept": "application/xml, text/xml, */*",
}

# XML namespaces used in sitemaps
NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
    "video": "http://www.google.com/schemas/sitemap-video/1.1",
}


def discover_sitemap_urls(base_url: str) -> list[str]:
    """Discover sitemap URLs for a domain."""
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    candidates = [
        f"{domain}/sitemap.xml",
        f"{domain}/sitemap_index.xml",
        f"{domain}/sitemap-news.xml",
        f"{domain}/news-sitemap.xml",
        f"{domain}/post-sitemap.xml",
        f"{domain}/sitemap-posts.xml",
    ]

    found = []
    for url in candidates:
        try:
            resp = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                found.append(url)
        except requests.RequestException:
            continue

    return found


def parse_sitemap(sitemap_url: str, max_age_days: int = 7, max_urls: int = 200) -> list[dict]:
    """
    Parse a sitemap and return recent article URLs with metadata.

    Returns list of dicts with: url, title (if news sitemap), published_at, images
    """
    try:
        resp = requests.get(sitemap_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch sitemap {sitemap_url}: {e}")
        return []

    try:
        root = ElementTree.fromstring(resp.content)
    except ElementTree.ParseError as e:
        logger.warning(f"Failed to parse sitemap XML {sitemap_url}: {e}")
        return []

    # Check if it's a sitemap index
    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag == "sitemapindex":
        return _parse_sitemap_index(root, max_age_days, max_urls)

    return _parse_urlset(root, max_age_days, max_urls)


def _parse_sitemap_index(root, max_age_days: int, max_urls: int) -> list[dict]:
    """Parse a sitemap index file and recurse into child sitemaps."""
    articles = []
    for sitemap in root.findall("sm:sitemap", NS):
        loc = sitemap.find("sm:loc", NS)
        if loc is None or loc.text is None:
            continue

        lastmod = sitemap.find("sm:lastmod", NS)
        if lastmod is not None and lastmod.text:
            mod_date = _parse_sitemap_date(lastmod.text)
            if mod_date and _is_too_old(mod_date, max_age_days):
                continue

        child_articles = parse_sitemap(loc.text.strip(), max_age_days, max_urls - len(articles))
        articles.extend(child_articles)

        if len(articles) >= max_urls:
            break

    return articles[:max_urls]


def _parse_urlset(root, max_age_days: int, max_urls: int) -> list[dict]:
    """Parse a URL set sitemap."""
    articles = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

    for url_el in root.findall("sm:url", NS):
        loc = url_el.find("sm:loc", NS)
        if loc is None or loc.text is None:
            continue

        url = loc.text.strip()
        entry = {"url": url}

        # Last modified
        lastmod = url_el.find("sm:lastmod", NS)
        if lastmod is not None and lastmod.text:
            mod_date = _parse_sitemap_date(lastmod.text)
            if mod_date:
                if _is_too_old(mod_date, max_age_days):
                    continue
                entry["published_at"] = mod_date.isoformat()

        # Google News sitemap extensions
        news = url_el.find("news:news", NS)
        if news is not None:
            title_el = news.find("news:title", NS)
            if title_el is not None and title_el.text:
                entry["title"] = title_el.text.strip()

            pub_date = news.find("news:publication_date", NS)
            if pub_date is not None and pub_date.text:
                entry["published_at"] = pub_date.text.strip()

            keywords_el = news.find("news:keywords", NS)
            if keywords_el is not None and keywords_el.text:
                entry["tags"] = [k.strip() for k in keywords_el.text.split(",")]

        # Image sitemap extensions
        images = []
        for img in url_el.findall("image:image", NS):
            img_loc = img.find("image:loc", NS)
            if img_loc is not None and img_loc.text:
                img_entry = {"url": img_loc.text.strip()}
                img_title = img.find("image:title", NS)
                if img_title is not None and img_title.text:
                    img_entry["alt"] = img_title.text.strip()
                images.append(img_entry)
        if images:
            entry["images"] = images
            entry["featured_image_url"] = images[0]["url"]

        articles.append(entry)
        if len(articles) >= max_urls:
            break

    return articles


def _parse_sitemap_date(date_str: str) -> Optional[datetime]:
    """Parse sitemap date formats."""
    clean = date_str.strip()

    # Formats with timezone info (%z) - don't add tzinfo manually
    tz_formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    ]
    for fmt in tz_formats:
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue

    # Formats without timezone - assume UTC
    naive_formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in naive_formats:
        try:
            return datetime.strptime(clean, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _is_too_old(dt: datetime, max_age_days: int) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt < cutoff
