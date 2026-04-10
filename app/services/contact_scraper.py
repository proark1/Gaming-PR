"""
Contact Scraper Service
Scrapes websites of outlets, streamers, and gaming VCs to enrich their profiles
with additional data like social links, contact info, descriptions, and metadata.
"""
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.outlet import GamingOutlet
from app.models.streamer import Streamer
from app.models.gaming_vc import GamingVC

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

# ─── Helper Functions ───

def _fetch_page(url: str, timeout: int = 20) -> Optional[BeautifulSoup]:
    """Fetch and parse a web page."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def _extract_emails(soup: BeautifulSoup, text: str) -> list[str]:
    """Extract email addresses from page content."""
    emails = set()
    # From mailto links
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip()
            if "@" in email:
                emails.add(email.lower())
    # From text using regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    for match in re.findall(email_pattern, text):
        # Filter out common false positives
        if not any(x in match.lower() for x in ["example.com", "email.com", "domain.com", ".png", ".jpg", ".gif"]):
            emails.add(match.lower())
    return list(emails)


def _extract_social_links(soup: BeautifulSoup, base_url: str) -> dict:
    """Extract social media links from a page."""
    social = {}
    patterns = {
        "twitter": [r"twitter\.com/([^/?\"']+)", r"x\.com/([^/?\"']+)"],
        "instagram": [r"instagram\.com/([^/?\"']+)"],
        "youtube": [r"youtube\.com/(c/|channel/|user/|@)([^/?\"']+)"],
        "facebook": [r"facebook\.com/([^/?\"']+)"],
        "linkedin": [r"linkedin\.com/(company|in)/([^/?\"']+)"],
        "twitch": [r"twitch\.tv/([^/?\"']+)"],
        "discord": [r"discord\.(gg|com/invite)/([^/?\"']+)"],
        "tiktok": [r"tiktok\.com/@([^/?\"']+)"],
        "crunchbase": [r"crunchbase\.com/organization/([^/?\"']+)"],
    }
    page_text = str(soup)
    for platform, regexes in patterns.items():
        for regex in regexes:
            match = re.search(regex, page_text, re.IGNORECASE)
            if match:
                social[platform] = match.group(0)
                break
    return social


def _extract_meta(soup: BeautifulSoup) -> dict:
    """Extract meta tags and structured data."""
    meta = {}
    # OG tags
    for tag in soup.find_all("meta", property=True):
        prop = tag.get("property", "")
        if prop.startswith("og:"):
            meta[prop] = tag.get("content", "")
    # Standard meta
    desc_tag = soup.find("meta", {"name": "description"})
    if desc_tag:
        meta["description"] = desc_tag.get("content", "")
    # Favicon
    icon = soup.find("link", rel=lambda r: r and "icon" in r)
    if icon and icon.get("href"):
        meta["favicon"] = icon["href"]
    # Logo (from JSON-LD)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                if data.get("logo"):
                    logo = data["logo"]
                    meta["logo"] = logo if isinstance(logo, str) else logo.get("url", "")
                if data.get("name"):
                    meta["org_name"] = data["name"]
        except (json.JSONDecodeError, AttributeError):
            pass
    return meta


def _extract_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract the site's about/description."""
    # Try meta description first
    desc_tag = soup.find("meta", {"name": "description"})
    if desc_tag and desc_tag.get("content"):
        return desc_tag["content"].strip()
    # Try OG description
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        return og_desc["content"].strip()
    return None


def _find_about_page(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Find the About page URL from navigation links."""
    about_keywords = ["about", "about-us", "about us", "who we are", "team", "our-story"]
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        text = link.get_text(strip=True).lower()
        if any(kw in href or kw in text for kw in about_keywords):
            return urljoin(base_url, link["href"])
    return None


def _find_contact_page(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Find the Contact page URL from navigation links."""
    contact_keywords = ["contact", "contact-us", "press", "media", "advertise", "pitch", "submit"]
    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        text = link.get_text(strip=True).lower()
        if any(kw in href or kw in text for kw in contact_keywords):
            return urljoin(base_url, link["href"])
    return None


# ─── Outlet Scraper ───

def scrape_outlet_website(db: Session, outlet_id: int) -> dict:
    """Scrape an outlet's website for additional details."""
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        return {"error": "Outlet not found"}

    result = {"outlet_id": outlet_id, "outlet_name": outlet.name, "data_found": {}, "errors": []}
    soup = _fetch_page(outlet.url)
    if not soup:
        result["errors"].append(f"Failed to fetch {outlet.url}")
        return result

    page_text = soup.get_text(separator=" ", strip=True)

    # Extract meta info
    meta = _extract_meta(soup)
    if meta.get("description") and not outlet.description:
        outlet.description = meta["description"]
        result["data_found"]["description"] = meta["description"]
    if meta.get("favicon"):
        favicon = meta["favicon"]
        if not favicon.startswith("http"):
            favicon = urljoin(outlet.url, favicon)
        outlet.favicon_url = favicon
        result["data_found"]["favicon_url"] = favicon
    if meta.get("logo"):
        logo = meta["logo"]
        if not logo.startswith("http"):
            logo = urljoin(outlet.url, logo)
        outlet.logo_url = logo
        result["data_found"]["logo_url"] = logo

    # Extract social links
    social = _extract_social_links(soup, outlet.url)
    if social.get("twitter") and not outlet.social_twitter:
        outlet.social_twitter = social["twitter"]
        result["data_found"]["social_twitter"] = social["twitter"]
    if social.get("facebook") and not outlet.social_facebook:
        outlet.social_facebook = social["facebook"]
        result["data_found"]["social_facebook"] = social["facebook"]
    if social.get("youtube") and not outlet.social_youtube:
        outlet.social_youtube = social["youtube"]
        result["data_found"]["social_youtube"] = social["youtube"]
    if social.get("instagram") and not outlet.social_instagram:
        outlet.social_instagram = social["instagram"]
        result["data_found"]["social_instagram"] = social["instagram"]
    if social.get("discord") and not outlet.social_discord:
        outlet.social_discord = social["discord"]
        result["data_found"]["social_discord"] = social["discord"]
    if social.get("tiktok") and not outlet.social_tiktok:
        outlet.social_tiktok = social["tiktok"]
        result["data_found"]["social_tiktok"] = social["tiktok"]

    # Extract emails
    emails = _extract_emails(soup, page_text)

    # Try to find contact/press page
    contact_url = _find_contact_page(soup, outlet.url)
    if contact_url:
        result["data_found"]["press_page_url"] = contact_url
        outlet.press_page_url = contact_url
        contact_soup = _fetch_page(contact_url)
        if contact_soup:
            contact_text = contact_soup.get_text(separator=" ", strip=True)
            emails.extend(_extract_emails(contact_soup, contact_text))
            social2 = _extract_social_links(contact_soup, outlet.url)
            social.update({k: v for k, v in social2.items() if k not in social})

    # Try to find about page for more info
    about_url = _find_about_page(soup, outlet.url)
    if about_url:
        about_soup = _fetch_page(about_url)
        if about_soup:
            about_text = about_soup.get_text(separator=" ", strip=True)
            emails.extend(_extract_emails(about_soup, about_text))
            if not outlet.description:
                desc = _extract_description(about_soup)
                if desc:
                    outlet.description = desc
                    result["data_found"]["description"] = desc

    # Assign emails
    if emails:
        unique_emails = list(set(emails))
        if not outlet.contact_email and unique_emails:
            # Prioritize press/media/editorial emails
            press_emails = [e for e in unique_emails if any(kw in e for kw in ["press", "media", "editor", "editorial", "news", "tips"])]
            outlet.contact_email = press_emails[0] if press_emails else unique_emails[0]
            result["data_found"]["contact_email"] = outlet.contact_email
        if not outlet.submission_email:
            submit_emails = [e for e in unique_emails if any(kw in e for kw in ["submit", "pitch", "press", "tips"])]
            if submit_emails:
                outlet.submission_email = submit_emails[0]
                result["data_found"]["submission_email"] = outlet.submission_email

    # Store raw scraped data
    outlet.scraped_data = {"meta": meta, "social": social, "emails": list(set(emails)), "contact_url": contact_url, "about_url": about_url}
    outlet.last_scraped_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(outlet)
    return result


# ─── Streamer Scraper ───

def scrape_streamer_website(db: Session, streamer_id: int) -> dict:
    """Scrape a streamer's pages for additional details."""
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        return {"error": "Streamer not found"}

    result = {"streamer_id": streamer_id, "streamer_name": streamer.name, "data_found": {}, "errors": []}
    soup = _fetch_page(streamer.url)
    if not soup:
        result["errors"].append(f"Failed to fetch {streamer.url}")
        return result

    page_text = soup.get_text(separator=" ", strip=True)

    # Extract meta info
    meta = _extract_meta(soup)
    if meta.get("og:image") and not streamer.profile_image_url:
        streamer.profile_image_url = meta["og:image"]
        result["data_found"]["profile_image_url"] = meta["og:image"]
    if meta.get("og:description") and not streamer.bio:
        streamer.bio = meta["og:description"]
        result["data_found"]["bio"] = meta["og:description"]

    # Extract social links
    social = _extract_social_links(soup, streamer.url)
    if social.get("twitter") and not streamer.social_twitter:
        streamer.social_twitter = social["twitter"]
        result["data_found"]["social_twitter"] = social["twitter"]
    if social.get("instagram") and not streamer.social_instagram:
        streamer.social_instagram = social["instagram"]
        result["data_found"]["social_instagram"] = social["instagram"]
    if social.get("youtube") and not streamer.social_youtube:
        streamer.social_youtube = social["youtube"]
        result["data_found"]["social_youtube"] = social["youtube"]
    if social.get("discord") and not streamer.social_discord:
        streamer.social_discord = social["discord"]
        result["data_found"]["social_discord"] = social["discord"]
    if social.get("tiktok") and not streamer.social_tiktok:
        streamer.social_tiktok = social["tiktok"]
        result["data_found"]["social_tiktok"] = social["tiktok"]

    # Extract emails
    emails = _extract_emails(soup, page_text)
    if emails and not streamer.contact_email:
        biz_emails = [e for e in emails if any(kw in e for kw in ["business", "biz", "collab", "partner", "sponsor"])]
        streamer.contact_email = biz_emails[0] if biz_emails else emails[0]
        result["data_found"]["contact_email"] = streamer.contact_email

    # Store raw scraped data
    streamer.scraped_data = {"meta": meta, "social": social, "emails": emails}
    streamer.last_scraped_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(streamer)
    return result


# ─── Gaming VC Scraper ───

def scrape_vc_website(db: Session, vc_id: int) -> dict:
    """Scrape a gaming VC's website for additional details."""
    vc = db.query(GamingVC).filter(GamingVC.id == vc_id).first()
    if not vc:
        return {"error": "Gaming VC not found"}

    result = {"vc_id": vc_id, "vc_name": vc.name, "data_found": {}, "errors": []}
    soup = _fetch_page(vc.url)
    if not soup:
        result["errors"].append(f"Failed to fetch {vc.url}")
        return result

    page_text = soup.get_text(separator=" ", strip=True)

    # Extract meta info
    meta = _extract_meta(soup)
    if meta.get("og:image") and not vc.logo_url:
        vc.logo_url = meta["og:image"]
        result["data_found"]["logo_url"] = meta["og:image"]
    if meta.get("description") and not vc.description:
        vc.description = meta["description"]
        result["data_found"]["description"] = meta["description"]

    # Extract social links
    social = _extract_social_links(soup, vc.url)
    if social.get("twitter") and not vc.social_twitter:
        vc.social_twitter = social["twitter"]
        result["data_found"]["social_twitter"] = social["twitter"]
    if social.get("linkedin") and not vc.social_linkedin:
        vc.social_linkedin = social["linkedin"]
        result["data_found"]["social_linkedin"] = social["linkedin"]
    if social.get("crunchbase") and not vc.social_crunchbase:
        vc.social_crunchbase = social["crunchbase"]
        result["data_found"]["social_crunchbase"] = social["crunchbase"]

    # Extract emails
    emails = _extract_emails(soup, page_text)

    # Try to find portfolio/about pages for more info
    about_url = _find_about_page(soup, vc.url)
    if about_url:
        about_soup = _fetch_page(about_url)
        if about_soup:
            about_text = about_soup.get_text(separator=" ", strip=True)
            emails.extend(_extract_emails(about_soup, about_text))
            if not vc.description:
                desc = _extract_description(about_soup)
                if desc:
                    vc.description = desc
                    result["data_found"]["description"] = desc

    # Look for pitch/contact page
    contact_url = _find_contact_page(soup, vc.url)
    if contact_url:
        contact_soup = _fetch_page(contact_url)
        if contact_soup:
            contact_text = contact_soup.get_text(separator=" ", strip=True)
            emails.extend(_extract_emails(contact_soup, contact_text))
            if not vc.pitch_form_url:
                # Look for form URLs
                forms = contact_soup.find_all("form")
                if forms:
                    vc.pitch_form_url = contact_url
                    result["data_found"]["pitch_form_url"] = contact_url

    # Look for portfolio page
    for link in soup.find_all("a", href=True):
        href_lower = link["href"].lower()
        text_lower = link.get_text(strip=True).lower()
        if any(kw in href_lower or kw in text_lower for kw in ["portfolio", "companies", "investments"]):
            portfolio_url = urljoin(vc.url, link["href"])
            portfolio_soup = _fetch_page(portfolio_url)
            if portfolio_soup:
                portfolio_text = portfolio_soup.get_text(separator=" ", strip=True)
                emails.extend(_extract_emails(portfolio_soup, portfolio_text))
            break

    # Look for blog/newsletter links
    for link in soup.find_all("a", href=True):
        href_lower = link["href"].lower()
        text_lower = link.get_text(strip=True).lower()
        if any(kw in href_lower or kw in text_lower for kw in ["blog", "insights", "thoughts"]):
            if not vc.blog_url:
                vc.blog_url = urljoin(vc.url, link["href"])
                result["data_found"]["blog_url"] = vc.blog_url
            break
    for link in soup.find_all("a", href=True):
        href_lower = link["href"].lower()
        text_lower = link.get_text(strip=True).lower()
        if any(kw in href_lower or kw in text_lower for kw in ["newsletter", "subscribe"]):
            if not vc.newsletter_url:
                vc.newsletter_url = urljoin(vc.url, link["href"])
                result["data_found"]["newsletter_url"] = vc.newsletter_url
            break

    # Assign emails
    if emails:
        unique_emails = list(set(emails))
        if not vc.contact_email and unique_emails:
            vc.contact_email = unique_emails[0]
            result["data_found"]["contact_email"] = vc.contact_email
        if not vc.pitch_email:
            pitch_emails = [e for e in unique_emails if any(kw in e for kw in ["pitch", "deal", "invest", "submit"])]
            if pitch_emails:
                vc.pitch_email = pitch_emails[0]
                result["data_found"]["pitch_email"] = vc.pitch_email

    # Store raw scraped data
    vc.scraped_data = {"meta": meta, "social": social, "emails": list(set(emails)), "contact_url": contact_url, "about_url": about_url}
    vc.last_scraped_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(vc)
    return result


# ─── Bulk Scraping ───

def scrape_all_outlets(db: Session) -> dict:
    """Scrape all active outlets' websites."""
    outlets = db.query(GamingOutlet).filter(GamingOutlet.is_active.is_(True)).all()
    results = {"total": len(outlets), "scraped": 0, "errors": 0, "details": []}
    for outlet in outlets:
        try:
            r = scrape_outlet_website(db, outlet.id)
            results["scraped"] += 1
            results["details"].append(r)
        except Exception as e:
            results["errors"] += 1
            results["details"].append({"outlet_id": outlet.id, "error": str(e)})
    return results


def scrape_all_streamers(db: Session) -> dict:
    """Scrape all active streamers' websites."""
    streamers = db.query(Streamer).filter(Streamer.is_active.is_(True)).all()
    results = {"total": len(streamers), "scraped": 0, "errors": 0, "details": []}
    for s in streamers:
        try:
            r = scrape_streamer_website(db, s.id)
            results["scraped"] += 1
            results["details"].append(r)
        except Exception as e:
            results["errors"] += 1
            results["details"].append({"streamer_id": s.id, "error": str(e)})
    return results


def scrape_all_vcs(db: Session) -> dict:
    """Scrape all active VCs' websites."""
    vcs = db.query(GamingVC).filter(GamingVC.is_active.is_(True)).all()
    results = {"total": len(vcs), "scraped": 0, "errors": 0, "details": []}
    for vc in vcs:
        try:
            r = scrape_vc_website(db, vc.id)
            results["scraped"] += 1
            results["details"].append(r)
        except Exception as e:
            results["errors"] += 1
            results["details"].append({"vc_id": vc.id, "error": str(e)})
    return results
