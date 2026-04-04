"""
Full article content extractor.

Fetches an article URL, extracts the complete body text, images, metadata,
OpenGraph tags, JSON-LD structured data, author info, tags, and everything
else that can be pulled from the page.
"""
import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Comment

from app.scrapers.constants import DEFAULT_HEADERS
from app.scrapers.stealth import get_stealth_headers, get_session_headers

logger = logging.getLogger(__name__)

# Fallback headers (used when stealth is disabled)
HEADERS = DEFAULT_HEADERS

GAMING_PLATFORMS = [
    "PS5", "PS4", "PlayStation 5", "PlayStation 4", "PlayStation",
    "Xbox Series X", "Xbox Series S", "Xbox One", "Xbox",
    "Nintendo Switch", "Switch", "Nintendo",
    "PC", "Steam", "Epic Games", "GOG",
    "iOS", "Android", "Mobile",
    "VR", "PSVR2", "Meta Quest", "Steam Deck",
]

ARTICLE_TYPES = {
    "review": ["review", "análisis", "test", "レビュー", "обзор", "critique", "reseña"],
    "preview": ["preview", "avance", "プレビュー", "превью", "aperçu"],
    "news": ["news", "noticia", "ニュース", "новость", "actualité", "خبر"],
    "guide": ["guide", "guía", "ガイド", "гайд", "astuce", "walkthrough", "tips"],
    "opinion": ["opinion", "editorial", "column", "コラム", "мнение"],
    "interview": ["interview", "entrevista", "インタビュー", "интервью"],
    "feature": ["feature", "reportaje", "特集", "спецматериал"],
    "list": ["top", "best", "ranking", "list"],
    "deal": ["deal", "sale", "discount", "oferta", "セール"],
    "trailer": ["trailer", "tráiler", "トレーラー", "трейлер"],
}

# CSS selectors for article body, ordered by specificity
CONTENT_SELECTORS = [
    "article .article-body",
    "article .entry-content",
    "article .post-content",
    "article .article-content",
    ".article-body",
    ".entry-content",
    ".post-content",
    ".article-content",
    ".story-body",
    ".news-article-body",
    ".review-body",
    '[itemprop="articleBody"]',
    '[property="articleBody"]',
    ".content-body",
    ".article__body",
    ".article-text",
    ".body-text",
    ".text-body",
    "article .content",
    ".post-entry",
    "article",
    ".post",
    '[role="main"] .content',
    "main .content",
]

# Elements to remove before extracting text
STRIP_TAGS = [
    "script", "style", "nav", "footer", "header", "aside",
    "iframe", "noscript", "form", "button", "svg",
    ".ad", ".ads", ".advertisement", ".social-share",
    ".related-articles", ".recommended", ".sidebar",
    ".newsletter", ".comments", ".comment-section",
    ".cookie-banner", ".popup", ".modal",
    "[data-ad]", "[data-advertisement]",
]


def extract_full_article(url: str, timeout: int = 20, language: str = "en",
                         use_stealth: bool = True, use_browser_fallback: bool = True) -> dict:
    """
    Extract everything possible from an article URL.

    Returns a dict with all extracted data. Never raises - returns
    partial data with errors logged in the 'extraction_errors' field.

    Features stealth headers and Playwright browser fallback for JS-heavy sites.
    """
    result = {
        "url": url,
        "canonical_url": None,
        "title": None,
        "full_body_html": None,
        "full_body_text": None,
        "summary": None,
        "word_count": None,
        "reading_time_minutes": None,
        "author": None,
        "author_url": None,
        "authors": [],
        "published_at": None,
        "updated_at": None,
        "featured_image_url": None,
        "thumbnail_url": None,
        "images": [],
        "video_url": None,
        "videos": [],
        "categories": [],
        "tags": [],
        "article_type": None,
        "game_titles": [],
        "platforms": [],
        "meta_title": None,
        "meta_description": None,
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "og_type": None,
        "twitter_card": None,
        "structured_data": None,
        "comment_count": None,
        "rating_score": None,
        "rating_max": None,
        "content_hash": None,
        "http_status_code": None,
        "is_full_content": False,
        "extraction_errors": [],
        "rendered_by": "requests",  # Track which method got the content
    }

    # Use stealth headers if enabled
    headers = HEADERS
    if use_stealth:
        try:
            domain = urlparse(url).netloc
            headers = get_session_headers(domain, language=language)
        except Exception as e:
            logger.debug(f"Stealth headers failed for {url}, using defaults: {e}")

    html_text = None

    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        result["http_status_code"] = response.status_code
        response.raise_for_status()
        html_text = response.text
    except requests.RequestException as e:
        result["extraction_errors"].append(f"HTTP request failed: {e}")

    # Browser fallback for JS-heavy sites or failed requests
    if use_browser_fallback and (html_text is None or _needs_browser_check(url, html_text)):
        try:
            from app.scrapers.browser import fetch_with_browser, is_playwright_available
            if is_playwright_available():
                browser_result = fetch_with_browser(url, timeout=timeout * 1000)
                if browser_result and browser_result.get("html"):
                    html_text = browser_result["html"]
                    result["http_status_code"] = browser_result.get("status_code", 200)
                    result["rendered_by"] = "playwright"
        except Exception as e:
            result["extraction_errors"].append(f"Browser fallback failed: {e}")

    if not html_text:
        return result

    try:
        soup = BeautifulSoup(html_text, "lxml")
    except Exception as e:
        logger.debug(f"lxml parser failed, falling back to html.parser: {e}")
        soup = BeautifulSoup(html_text, "html.parser")

    # Extract everything in parallel sections
    _extract_meta_tags(soup, url, result)
    _extract_opengraph(soup, result)
    _extract_twitter_card(soup, result)
    _extract_json_ld(soup, result)
    _extract_authors(soup, url, result)
    _extract_dates(soup, result)
    _extract_body_content(soup, url, result)
    _extract_images(soup, url, result)
    _extract_videos(soup, url, result)
    _extract_tags_and_categories(soup, result)
    _detect_article_type(result)
    _detect_platforms(result)
    _detect_game_titles(soup, result)
    _extract_engagement(soup, result)

    # Compute content hash for change detection
    if result["full_body_text"]:
        result["content_hash"] = hashlib.sha256(result["full_body_text"].encode()).hexdigest()
        result["is_full_content"] = True

    return result


def _extract_meta_tags(soup: BeautifulSoup, url: str, result: dict):
    """Extract standard HTML meta tags."""
    try:
        title_tag = soup.find("title")
        if title_tag:
            result["meta_title"] = title_tag.get_text(strip=True)
            if not result["title"]:
                result["title"] = result["meta_title"]

        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            result["meta_description"] = desc.get("content", "")

        canonical = soup.find("link", attrs={"rel": "canonical"})
        if canonical:
            result["canonical_url"] = canonical.get("href")

        # Author from meta
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and not result["author"]:
            result["author"] = author_meta.get("content", "")

        # Keywords
        keywords_meta = soup.find("meta", attrs={"name": "keywords"})
        if keywords_meta:
            kw = keywords_meta.get("content", "")
            if kw:
                result["tags"].extend([k.strip() for k in kw.split(",") if k.strip()])

    except Exception as e:
        result["extraction_errors"].append(f"Meta extraction: {e}")


def _extract_opengraph(soup: BeautifulSoup, result: dict):
    """Extract OpenGraph metadata."""
    try:
        og_tags = {}
        for meta in soup.find_all("meta", attrs={"property": re.compile(r"^og:")}):
            prop = meta.get("property", "")
            content = meta.get("content", "")
            if prop and content:
                og_tags[prop] = content

        result["og_title"] = og_tags.get("og:title")
        result["og_description"] = og_tags.get("og:description")
        result["og_image"] = og_tags.get("og:image")
        result["og_type"] = og_tags.get("og:type")

        if not result["title"] and result["og_title"]:
            result["title"] = result["og_title"]
        if not result["summary"] and result["og_description"]:
            result["summary"] = result["og_description"]

        # og:video
        if "og:video" in og_tags or "og:video:url" in og_tags:
            result["video_url"] = og_tags.get("og:video") or og_tags.get("og:video:url")

    except Exception as e:
        result["extraction_errors"].append(f"OpenGraph extraction: {e}")


def _extract_twitter_card(soup: BeautifulSoup, result: dict):
    """Extract Twitter Card metadata."""
    try:
        tc = soup.find("meta", attrs={"name": "twitter:card"})
        if tc:
            result["twitter_card"] = tc.get("content")

        if not result["featured_image_url"]:
            tw_img = soup.find("meta", attrs={"name": "twitter:image"})
            if tw_img:
                result["featured_image_url"] = tw_img.get("content")

    except Exception as e:
        result["extraction_errors"].append(f"Twitter card extraction: {e}")


def _extract_json_ld(soup: BeautifulSoup, result: dict):
    """Extract JSON-LD structured data (Schema.org)."""
    try:
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        structured = []

        for script in scripts:
            try:
                data = json.loads(script.string or "")
                structured.append(data)
                _parse_json_ld_article(data, result)
            except (json.JSONDecodeError, TypeError):
                continue

        if structured:
            result["structured_data"] = structured if len(structured) > 1 else structured[0]

    except Exception as e:
        result["extraction_errors"].append(f"JSON-LD extraction: {e}")


def _parse_json_ld_article(data: dict, result: dict):
    """Extract article-specific fields from JSON-LD."""
    if isinstance(data, list):
        for item in data:
            _parse_json_ld_article(item, result)
        return

    if not isinstance(data, dict):
        return

    schema_type = data.get("@type", "")
    if isinstance(schema_type, list):
        schema_type = schema_type[0] if schema_type else ""

    article_types = ["Article", "NewsArticle", "BlogPosting", "Review", "WebPage"]
    if schema_type not in article_types:
        if "@graph" in data:
            for item in data["@graph"]:
                _parse_json_ld_article(item, result)
        return

    if not result["title"] and data.get("headline"):
        result["title"] = data["headline"]

    if not result["summary"] and data.get("description"):
        result["summary"] = data["description"]

    if not result["featured_image_url"]:
        img = data.get("image")
        if isinstance(img, str):
            result["featured_image_url"] = img
        elif isinstance(img, dict):
            result["featured_image_url"] = img.get("url")
        elif isinstance(img, list) and img:
            first = img[0]
            result["featured_image_url"] = first if isinstance(first, str) else first.get("url", "")

    # Author from JSON-LD
    author = data.get("author")
    if author:
        if isinstance(author, dict):
            name = author.get("name", "")
            if name and not result["author"]:
                result["author"] = name
                result["authors"].append({"name": name, "url": author.get("url")})
        elif isinstance(author, list):
            for a in author:
                if isinstance(a, dict):
                    result["authors"].append({"name": a.get("name", ""), "url": a.get("url")})
            if result["authors"] and not result["author"]:
                result["author"] = result["authors"][0].get("name", "")

    # Dates from JSON-LD
    if not result["published_at"] and data.get("datePublished"):
        result["published_at"] = _parse_date_string(data["datePublished"])
    if not result["updated_at"] and data.get("dateModified"):
        result["updated_at"] = _parse_date_string(data["dateModified"])

    # Review score
    if schema_type == "Review" and data.get("reviewRating"):
        rating = data["reviewRating"]
        result["rating_score"] = _safe_float(rating.get("ratingValue"))
        result["rating_max"] = _safe_float(rating.get("bestRating", 10))

    # Comment count
    if data.get("commentCount"):
        try:
            result["comment_count"] = int(data["commentCount"])
        except (ValueError, TypeError):
            pass


def _extract_authors(soup: BeautifulSoup, url: str, result: dict):
    """Extract author information from various page elements."""
    if result["author"]:
        return

    try:
        # Schema.org itemprop
        author_el = soup.find(attrs={"itemprop": "author"})
        if author_el:
            name_el = author_el.find(attrs={"itemprop": "name"})
            result["author"] = (name_el or author_el).get_text(strip=True)
            link = author_el.find("a")
            if link and link.get("href"):
                result["author_url"] = urljoin(url, link["href"])
            return

        # Common CSS patterns
        author_selectors = [
            ".author-name", ".byline", ".article-author",
            '[rel="author"]', ".writer", ".post-author",
            ".author a", ".byline a",
        ]
        for selector in author_selectors:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) < 200:
                    result["author"] = text.removeprefix("By ").removeprefix("by ")
                    if el.name == "a" and el.get("href"):
                        result["author_url"] = urljoin(url, el["href"])
                    return

    except Exception as e:
        result["extraction_errors"].append(f"Author extraction: {e}")


def _extract_dates(soup: BeautifulSoup, result: dict):
    """Extract published/updated dates from page elements."""
    if result["published_at"]:
        return

    try:
        # time elements
        time_el = soup.find("time", attrs={"datetime": True})
        if time_el:
            result["published_at"] = _parse_date_string(time_el["datetime"])

        # itemprop datePublished
        pub_el = soup.find(attrs={"itemprop": "datePublished"})
        if pub_el and not result["published_at"]:
            dt = pub_el.get("content") or pub_el.get("datetime") or pub_el.get_text(strip=True)
            result["published_at"] = _parse_date_string(dt)

        mod_el = soup.find(attrs={"itemprop": "dateModified"})
        if mod_el and not result["updated_at"]:
            dt = mod_el.get("content") or mod_el.get("datetime") or mod_el.get_text(strip=True)
            result["updated_at"] = _parse_date_string(dt)

    except Exception as e:
        result["extraction_errors"].append(f"Date extraction: {e}")


def _extract_body_content(soup: BeautifulSoup, url: str, result: dict):
    """Extract the main article body text and HTML."""
    try:
        # Clean the soup of junk elements
        cleaned = _clean_soup(soup)

        # Try each content selector in order
        content_el = None
        for selector in CONTENT_SELECTORS:
            try:
                content_el = cleaned.select_one(selector)
                if content_el and len(content_el.get_text(strip=True)) > 100:
                    break
                content_el = None
            except Exception as e:
                logger.debug(f"Content selector '{selector}' failed: {e}")
                continue

        if not content_el:
            # Fallback: find the largest text block
            content_el = _find_largest_text_block(cleaned)

        if content_el:
            result["full_body_html"] = str(content_el)
            text = content_el.get_text(separator="\n", strip=True)
            result["full_body_text"] = _clean_text(text)

            words = len(result["full_body_text"].split())
            result["word_count"] = words
            result["reading_time_minutes"] = max(1, round(words / 250))

            if not result["summary"] and result["full_body_text"]:
                result["summary"] = result["full_body_text"][:500].rsplit(".", 1)[0] + "." if "." in result["full_body_text"][:500] else result["full_body_text"][:500]

    except Exception as e:
        result["extraction_errors"].append(f"Body extraction: {e}")


def _extract_images(soup: BeautifulSoup, url: str, result: dict):
    """Extract all images from the article."""
    try:
        images = []
        seen = set()

        # Featured image from og:image
        if result["og_image"] and result["og_image"] not in seen:
            result["featured_image_url"] = result["og_image"]
            seen.add(result["og_image"])
            images.append({
                "url": result["og_image"],
                "alt": result.get("og_title", ""),
                "is_featured": True,
            })

        # All article images
        for img in soup.find_all("img", src=True):
            src = img.get("src", "")
            if not src or src.startswith("data:"):
                continue

            # Try srcset for higher quality
            srcset = img.get("srcset", "")
            if srcset:
                best = _get_best_srcset(srcset)
                if best:
                    src = best

            full_url = urljoin(url, src)
            if full_url in seen:
                continue

            # Skip tiny images (icons, trackers)
            width = _safe_int(img.get("width"))
            height = _safe_int(img.get("height"))
            if width and width < 50:
                continue
            if height and height < 50:
                continue

            seen.add(full_url)
            images.append({
                "url": full_url,
                "alt": img.get("alt", ""),
                "width": width,
                "height": height,
            })

        result["images"] = images[:50]  # cap at 50

        if not result["featured_image_url"] and images:
            result["featured_image_url"] = images[0]["url"]

        if not result["thumbnail_url"] and result["featured_image_url"]:
            result["thumbnail_url"] = result["featured_image_url"]

    except Exception as e:
        result["extraction_errors"].append(f"Image extraction: {e}")


def _extract_videos(soup: BeautifulSoup, url: str, result: dict):
    """Extract video embeds from the article."""
    try:
        videos = []
        seen = set()

        for iframe in soup.find_all("iframe", src=True):
            src = iframe.get("src", "")
            if not src:
                continue
            full_url = urljoin(url, src)
            if full_url in seen:
                continue

            platform = _detect_video_platform(full_url)
            if platform:
                seen.add(full_url)
                videos.append({
                    "url": full_url,
                    "platform": platform,
                    "embed_url": full_url,
                })

        # Also check for <video> tags
        for video in soup.find_all("video"):
            src = video.get("src") or ""
            source = video.find("source")
            if source:
                src = source.get("src", src)
            if src:
                full_url = urljoin(url, src)
                if full_url not in seen:
                    seen.add(full_url)
                    videos.append({"url": full_url, "platform": "native"})

        result["videos"] = videos[:20]
        if not result["video_url"] and videos:
            result["video_url"] = videos[0]["url"]

    except Exception as e:
        result["extraction_errors"].append(f"Video extraction: {e}")


def _extract_tags_and_categories(soup: BeautifulSoup, result: dict):
    """Extract tags and categories from the page."""
    try:
        tag_selectors = [
            ".tags a", ".tag-list a", ".article-tags a",
            '[rel="tag"]', ".post-tags a", ".entry-tags a",
            ".topic a", ".topics a",
        ]
        tags = set(result.get("tags", []))
        for selector in tag_selectors:
            for el in soup.select(selector):
                text = el.get_text(strip=True)
                if text and len(text) < 100:
                    tags.add(text)

        cat_selectors = [
            ".category a", ".categories a", ".breadcrumb a",
            ".article-category a",
        ]
        categories = set(result.get("categories", []))
        for selector in cat_selectors:
            for el in soup.select(selector):
                text = el.get_text(strip=True)
                if text and len(text) < 100 and text.lower() not in ("home", "main"):
                    categories.add(text)

        result["tags"] = list(tags)[:50]
        result["categories"] = list(categories)[:20]

    except Exception as e:
        result["extraction_errors"].append(f"Tag extraction: {e}")


def _detect_article_type(result: dict):
    """Infer the article type from title, tags, URL, and categories."""
    searchable = " ".join([
        result.get("title") or "",
        result.get("url") or "",
        " ".join(result.get("tags", [])),
        " ".join(result.get("categories", [])),
    ]).lower()

    for atype, keywords in ARTICLE_TYPES.items():
        for kw in keywords:
            if kw.lower() in searchable:
                result["article_type"] = atype
                return


def _detect_platforms(result: dict):
    """Detect gaming platforms mentioned in the article."""
    searchable = " ".join([
        result.get("title") or "",
        result.get("full_body_text") or "",
        " ".join(result.get("tags", [])),
    ])

    platforms = set()
    for platform in GAMING_PLATFORMS:
        if platform.lower() in searchable.lower():
            platforms.add(platform)

    result["platforms"] = list(platforms)


def _detect_game_titles(soup: BeautifulSoup, result: dict):
    """Try to detect specific game titles from structured data and tags."""
    # From JSON-LD
    sd = result.get("structured_data")
    if isinstance(sd, dict) and sd.get("about"):
        about = sd["about"]
        if isinstance(about, dict) and about.get("name"):
            result["game_titles"].append(about["name"])
        elif isinstance(about, list):
            for item in about:
                if isinstance(item, dict) and item.get("name"):
                    result["game_titles"].append(item["name"])

    # From tags that look like game names (capitalized multi-word)
    for tag in result.get("tags", []):
        words = tag.split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if w.isalpha()):
            if tag not in result["game_titles"] and tag not in GAMING_PLATFORMS:
                result["game_titles"].append(tag)


def _extract_engagement(soup: BeautifulSoup, result: dict):
    """Extract engagement signals like comment count."""
    try:
        if result.get("comment_count") is not None:
            return

        comment_selectors = [".comment-count", ".comments-count", "#comment-count"]
        for selector in comment_selectors:
            el = soup.select_one(selector)
            if el:
                nums = re.findall(r"\d+", el.get_text())
                if nums:
                    result["comment_count"] = int(nums[0])
                    return

    except Exception as e:
        result["extraction_errors"].append(f"Engagement extraction: {e}")


# ── Helper functions ──


def _clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove noise elements from the soup for cleaner content extraction."""
    import copy
    cleaned = copy.deepcopy(soup)

    for selector in STRIP_TAGS:
        for el in cleaned.select(selector):
            el.decompose()

    for comment in cleaned.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    return cleaned


def _find_largest_text_block(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    """Find the DOM element with the most text content."""
    candidates = soup.find_all(["div", "section", "main", "article"])
    best = None
    best_len = 0

    for el in candidates:
        text = el.get_text(strip=True)
        if len(text) > best_len:
            best = el
            best_len = len(text)

    return best if best_len > 200 else None


def _clean_text(text: str) -> str:
    """Clean extracted text."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned.append(line)
    return "\n".join(cleaned)


def _get_best_srcset(srcset: str) -> Optional[str]:
    """Get the highest-resolution URL from a srcset attribute."""
    try:
        parts = srcset.split(",")
        best_url = ""
        best_width = 0
        for part in parts:
            tokens = part.strip().split()
            if len(tokens) >= 2:
                url = tokens[0]
                descriptor = tokens[1]
                if descriptor.endswith("w"):
                    width = int(descriptor[:-1])
                    if width > best_width:
                        best_width = width
                        best_url = url
        return best_url or None
    except Exception as e:
        logger.debug(f"Failed to parse srcset: {e}")
        return None


def _detect_video_platform(url: str) -> Optional[str]:
    """Detect if a URL is from a known video platform."""
    domain = urlparse(url).netloc.lower()
    if "youtube" in domain or "youtu.be" in domain:
        return "youtube"
    if "twitch" in domain:
        return "twitch"
    if "vimeo" in domain:
        return "vimeo"
    if "dailymotion" in domain:
        return "dailymotion"
    if "streamable" in domain:
        return "streamable"
    return None


def _parse_date_string(date_str: str) -> Optional[str]:
    """Try to parse a date string into ISO format. Returns string for DB flexibility."""
    if not date_str:
        return None

    from datetime import datetime

    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]

    # Strip timezone info for simple parsing
    clean = date_str.strip()

    for fmt in formats:
        try:
            return datetime.strptime(clean, fmt).isoformat()
        except ValueError:
            continue

    # Last resort: try dateutil if the string is reasonable
    try:
        if len(clean) < 100:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(clean).isoformat()
    except Exception as e:
        logger.debug(f"Date string parsing failed for '{date_str}': {e}")

    return None


def _safe_int(val) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _needs_browser_check(url: str, html_text: str) -> bool:
    """Check if the page likely needs browser rendering to get real content."""
    try:
        from app.scrapers.browser import needs_browser
        return needs_browser(url, html_text)
    except Exception as e:
        logger.debug(f"Browser check failed for {url}: {e}")
        return False
