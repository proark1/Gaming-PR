"""
robots.txt compliance - be a good citizen so we don't get blocked.
Caches parsed robots.txt per domain with TTL and max size limits.
"""
import logging
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

logger = logging.getLogger(__name__)

_CACHE_MAX_SIZE = 200
_CACHE_TTL_SECONDS = 3600  # 1 hour

_cache: dict[str, tuple[RobotFileParser | None, float]] = {}

USER_AGENT = "GamingPRBot/2.0"


def _get_cached(domain: str) -> RobotFileParser | None:
    """Get a cached RobotFileParser if it exists and hasn't expired."""
    entry = _cache.get(domain)
    if entry is None:
        return None
    rp, timestamp = entry
    if time.monotonic() - timestamp > _CACHE_TTL_SECONDS:
        del _cache[domain]
        return None
    return rp


def _set_cached(domain: str, rp: RobotFileParser | None):
    """Cache a RobotFileParser, evicting oldest entries if at capacity."""
    if len(_cache) >= _CACHE_MAX_SIZE:
        # Evict the oldest entry
        oldest_key = min(_cache, key=lambda k: _cache[k][1])
        del _cache[oldest_key]
    _cache[domain] = (rp, time.monotonic())


def can_fetch(url: str) -> bool:
    """Check if we're allowed to fetch this URL per robots.txt."""
    try:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        cached = _get_cached(domain)
        if cached is not None:
            return cached.can_fetch(USER_AGENT, url)

        if domain in _cache:
            # Cached as None (couldn't read robots.txt) - allow
            return True

        rp = RobotFileParser()
        robots_url = f"{domain}/robots.txt"
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception as e:
            logger.debug(f"Could not read robots.txt for {domain}: {e}")
            _set_cached(domain, None)
            return True
        _set_cached(domain, rp)

        return rp.can_fetch(USER_AGENT, url)

    except Exception as e:
        logger.debug(f"robots.txt check failed for {url}: {e}")
        return True  # fail open


def get_crawl_delay(url: str) -> float | None:
    """Get the crawl-delay for a domain, if specified."""
    try:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        cached = _get_cached(domain)
        if cached:
            delay = cached.crawl_delay(USER_AGENT) or cached.crawl_delay("*")
            return float(delay) if delay else None
    except Exception as e:
        logger.debug(f"Failed to get crawl delay for {url}: {e}")
    return None


def get_sitemaps(url: str) -> list[str]:
    """Get sitemap URLs declared in robots.txt."""
    try:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        cached = _get_cached(domain)
        if cached and hasattr(cached, "site_maps") and callable(cached.site_maps):
            maps = cached.site_maps()
            return maps if maps else []
    except Exception as e:
        logger.debug(f"Failed to get sitemaps for {url}: {e}")
    return []


def clear_cache():
    """Clear the robots.txt cache."""
    _cache.clear()
