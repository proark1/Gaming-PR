"""
User-Agent rotation and stealth request headers.

Rotates through realistic browser fingerprints to avoid detection.
"""
import random
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Realistic desktop User-Agents (Chrome, Firefox, Safari, Edge)
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Firefox on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

# Accept-Language headers for different locales
ACCEPT_LANGUAGES = {
    "en": "en-US,en;q=0.9",
    "zh-CN": "zh-CN,zh;q=0.9,en;q=0.8",
    "hi": "hi-IN,hi;q=0.9,en;q=0.8",
    "es": "es-ES,es;q=0.9,en;q=0.8",
    "fr": "fr-FR,fr;q=0.9,en;q=0.8",
    "ar": "ar-SA,ar;q=0.9,en;q=0.8",
    "bn": "bn-BD,bn;q=0.9,en;q=0.8",
    "pt": "pt-BR,pt;q=0.9,en;q=0.8",
    "ru": "ru-RU,ru;q=0.9,en;q=0.8",
    "ja": "ja-JP,ja;q=0.9,en;q=0.8",
}

# Referer strategies
REFERER_STRATEGIES = ["google", "direct", "social"]


def get_random_user_agent() -> str:
    """Get a random realistic User-Agent string."""
    return random.choice(USER_AGENTS)


def get_stealth_headers(
    language: str = "en",
    referer_url: Optional[str] = None,
) -> dict:
    """
    Generate a complete set of realistic browser headers.

    Rotates UA, sets proper Accept headers, matches language to outlet.
    """
    ua = get_random_user_agent()
    accept_lang = ACCEPT_LANGUAGES.get(language, ACCEPT_LANGUAGES["en"])

    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": accept_lang,
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none" if not referer_url else "cross-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    # Add a realistic referer
    if referer_url:
        headers["Referer"] = referer_url
    else:
        strategy = random.choice(REFERER_STRATEGIES)
        if strategy == "google":
            headers["Referer"] = "https://www.google.com/"
        elif strategy == "social":
            headers["Referer"] = random.choice([
                "https://twitter.com/",
                "https://www.reddit.com/",
                "https://news.ycombinator.com/",
            ])
        # "direct" = no referer

    # Randomly add sec-ch-ua headers (Chrome-based UAs)
    if "Chrome" in ua and "Firefox" not in ua and "Safari/605" not in ua:
        chrome_version = "124"
        for v in ["124", "123", "122"]:
            if v in ua:
                chrome_version = v
                break

        headers["sec-ch-ua"] = f'"Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}", "Not-A.Brand";v="99"'
        headers["sec-ch-ua-mobile"] = "?0"
        headers["sec-ch-ua-platform"] = '"Windows"' if "Windows" in ua else ('"macOS"' if "Mac" in ua else '"Linux"')

    return headers


# Per-domain header cache to maintain consistency within a session
_domain_sessions: dict[str, dict] = {}


def get_session_headers(domain: str, language: str = "en") -> dict:
    """
    Get consistent headers for a domain within the same scrape session.
    Uses the same UA for all requests to the same domain to look natural.
    """
    if domain not in _domain_sessions:
        _domain_sessions[domain] = get_stealth_headers(language=language)
    return _domain_sessions[domain]


def reset_sessions():
    """Reset all domain sessions (call between scrape runs)."""
    _domain_sessions.clear()
