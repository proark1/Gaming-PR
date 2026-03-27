"""
robots.txt compliance - be a good citizen so we don't get blocked.
Caches parsed robots.txt per domain to avoid re-fetching.
"""
import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)

_cache: dict[str, RobotFileParser] = {}

USER_AGENT = "GamingPRBot/2.0"


def can_fetch(url: str) -> bool:
    """Check if we're allowed to fetch this URL per robots.txt."""
    try:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain not in _cache:
            rp = RobotFileParser()
            robots_url = f"{domain}/robots.txt"
            rp.set_url(robots_url)
            try:
                rp.read()
            except Exception:
                # If we can't read robots.txt, assume allowed
                _cache[domain] = None
                return True
            _cache[domain] = rp

        rp = _cache[domain]
        if rp is None:
            return True

        # Check our specific bot UA first; fall back to wildcard rules
        return rp.can_fetch(USER_AGENT, url)

    except Exception as e:
        logger.debug(f"robots.txt check failed for {url}: {e}")
        return True  # fail open


def get_crawl_delay(url: str) -> float | None:
    """Get the crawl-delay for a domain, if specified."""
    try:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        rp = _cache.get(domain)
        if rp:
            delay = rp.crawl_delay(USER_AGENT) or rp.crawl_delay("*")
            return float(delay) if delay else None
    except Exception:
        pass
    return None


def get_sitemaps(url: str) -> list[str]:
    """Get sitemap URLs declared in robots.txt."""
    try:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        rp = _cache.get(domain)
        if rp and hasattr(rp, "site_maps") and callable(rp.site_maps):
            maps = rp.site_maps()
            return maps if maps else []
    except Exception:
        pass
    return []


def clear_cache():
    """Clear the robots.txt cache."""
    _cache.clear()
