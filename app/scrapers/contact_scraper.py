"""
Contact information scraper for gaming outlets.

Discovers email addresses, phone numbers, and contact page URLs
by scanning an outlet's homepage and common contact/about pages.
"""
import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.scrapers.stealth import get_stealth_headers

logger = logging.getLogger(__name__)

# Common paths where contact info lives
CONTACT_PATHS = [
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/impressum",       # German legal requirement (always has contact)
    "/imprint",
    "/team",
    "/advertise",
    "/advertising",
    "/legal",
    "/privacy",
]

# Email regex — match common email patterns, exclude images/assets
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# Phone regex — international formats
PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s\-.]?)?"        # optional country code
    r"(?:\(?\d{1,4}\)?[\s\-.]?)?"     # optional area code
    r"\d[\d\s\-\.]{6,14}\d",          # main number
)

# Emails to ignore (common false positives)
IGNORE_EMAIL_PATTERNS = {
    "example.com", "sentry.io", "wixpress.com", "schema.org",
    "w3.org", "wordpress.org", "gravatar.com", "googleapis.com",
    "creativecommons.org", "ogp.me", "purl.org",
}

# File extensions that aren't real emails
IGNORE_EMAIL_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js"}


def _is_valid_email(email: str) -> bool:
    """Filter out fake/irrelevant emails."""
    email = email.lower().strip()
    if len(email) > 254 or len(email) < 6:
        return False
    domain = email.split("@")[-1]
    if any(p in domain for p in IGNORE_EMAIL_PATTERNS):
        return False
    if any(email.endswith(s) for s in IGNORE_EMAIL_SUFFIXES):
        return False
    # Skip noreply/automated addresses
    local = email.split("@")[0]
    if local in ("noreply", "no-reply", "donotreply", "mailer-daemon", "postmaster"):
        return False
    return True


def _is_valid_phone(phone: str) -> bool:
    """Filter out numbers that aren't actual phone numbers."""
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) < 7 or len(digits) > 15:
        return False
    # Skip years, CSS values, IDs
    if re.match(r"^(19|20)\d{2}$", digits):
        return False
    return True


def _score_email(email: str) -> int:
    """Higher score = more likely to be the right contact email."""
    email = email.lower()
    local = email.split("@")[0]
    # Best: explicit contact addresses
    if local in ("contact", "info", "press", "media", "pr", "news", "editor", "editorial", "redaktion", "redaction"):
        return 100
    if "contact" in local or "press" in local or "media" in local or "pr" in local:
        return 80
    if local in ("hello", "hi", "team", "support", "general", "office"):
        return 60
    if local in ("ads", "advertising", "sales", "business", "marketing", "partnerships"):
        return 40
    # Generic personal emails are less useful
    return 20


def _fetch_page(url: str, timeout: int = 15) -> str | None:
    """Fetch a page with stealth headers and SSRF protection, return HTML or None."""
    from app.utils.url_safety import is_safe_url
    if not is_safe_url(url):
        logger.debug(f"Blocked unsafe URL: {url}")
        return None
    try:
        headers = get_stealth_headers(url)
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            return resp.text
    except Exception as e:
        logger.debug(f"Failed to fetch {url}: {e}")
    return None


def _extract_from_html(html: str, base_url: str) -> dict:
    """Extract emails and phones from HTML content."""
    soup = BeautifulSoup(html, "lxml")

    # Remove scripts and styles to avoid false positives
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    # Extract emails
    emails = set()
    # From mailto: links (highest confidence)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip()
            if _is_valid_email(email):
                emails.add(email.lower())
    # From text content
    for match in EMAIL_RE.findall(text):
        if _is_valid_email(match):
            emails.add(match.lower())

    # Extract phones
    phones = set()
    # From tel: links (highest confidence)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("tel:"):
            phone = href.replace("tel:", "").strip()
            if _is_valid_phone(phone):
                phones.add(phone)
    # From text — only look near keywords to reduce false positives
    phone_context_re = re.compile(
        r"(?:phone|tel|fax|call|telefon|téléphone|teléfono|電話|전화)[\s:.\-]*"
        r"((?:\+?\d[\d\s\-().]{6,16}\d))",
        re.IGNORECASE,
    )
    for match in phone_context_re.findall(text):
        if _is_valid_phone(match):
            phones.add(match.strip())

    # Find contact page link
    contact_url = None
    for a in soup.find_all("a", href=True):
        link_text = (a.get_text() or "").strip().lower()
        href = a["href"].lower()
        if any(kw in link_text for kw in ("contact", "kontakt", "contacto", "contato", "お問い合わせ", "문의")):
            contact_url = urljoin(base_url, a["href"])
            break
        if any(p in href for p in ("/contact", "/kontakt", "/about", "/impressum")):
            contact_url = urljoin(base_url, a["href"])
            break

    return {"emails": emails, "phones": phones, "contact_url": contact_url}


def scrape_outlet_contact(outlet_url: str, timeout: int = 15) -> dict:
    """
    Scrape contact info from an outlet's website.

    Returns:
        {
            "contact_email": "press@example.com" or None,
            "contact_phone": "+1-555-..." or None,
            "contact_page_url": "https://example.com/contact" or None,
        }
    """
    all_emails = set()
    all_phones = set()
    contact_page_url = None

    # Phase 1: Scan homepage
    html = _fetch_page(outlet_url, timeout)
    if html:
        result = _extract_from_html(html, outlet_url)
        all_emails.update(result["emails"])
        all_phones.update(result["phones"])
        if result["contact_url"]:
            contact_page_url = result["contact_url"]

    # Phase 2: Try common contact paths
    tried = {outlet_url}
    paths_to_try = list(CONTACT_PATHS)
    if contact_page_url and contact_page_url not in tried:
        paths_to_try.insert(0, None)  # placeholder — we'll use contact_page_url directly

    for path in paths_to_try:
        if path is None:
            url = contact_page_url
        else:
            url = urljoin(outlet_url.rstrip("/") + "/", path.lstrip("/"))

        if url in tried:
            continue
        tried.add(url)

        html = _fetch_page(url, timeout)
        if html:
            result = _extract_from_html(html, outlet_url)
            all_emails.update(result["emails"])
            all_phones.update(result["phones"])
            if not contact_page_url and result["contact_url"]:
                contact_page_url = result["contact_url"]

        # Stop early if we have good data
        if all_emails and all_phones:
            break

    # Pick best email by score
    best_email = None
    if all_emails:
        best_email = max(all_emails, key=_score_email)

    # Pick first phone
    best_phone = None
    if all_phones:
        best_phone = next(iter(all_phones))

    return {
        "contact_email": best_email,
        "contact_phone": best_phone,
        "contact_page_url": contact_page_url,
        "all_emails_found": list(all_emails),
        "all_phones_found": list(all_phones),
    }
