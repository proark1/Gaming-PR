"""
Playwright headless browser fallback for JS-rendered pages.

Falls back gracefully to requests if Playwright is not installed.
Used when standard HTTP requests fail to get meaningful content.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_playwright_available = None


def is_playwright_available() -> bool:
    """Check if Playwright is installed and usable."""
    global _playwright_available
    if _playwright_available is None:
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
            _playwright_available = True
        except ImportError:
            _playwright_available = False
            logger.info("Playwright not installed - JS rendering disabled")
    return _playwright_available


def fetch_with_browser(
    url: str,
    timeout: int = 30000,
    wait_for: str = "networkidle",
    user_agent: Optional[str] = None,
    extra_headers: Optional[dict] = None,
) -> Optional[dict]:
    """
    Fetch a page using a headless Chromium browser.

    Returns dict with 'html', 'status_code', 'final_url' or None on failure.
    """
    if not is_playwright_available():
        return None

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-default-apps",
                ],
            )

            context_kwargs = {
                "viewport": {"width": 1920, "height": 1080},
                "java_script_enabled": True,
                "bypass_csp": True,
            }
            if user_agent:
                context_kwargs["user_agent"] = user_agent
            if extra_headers:
                context_kwargs["extra_http_headers"] = extra_headers

            context = browser.new_context(**context_kwargs)
            context.set_default_timeout(timeout)

            page = context.new_page()

            # Block unnecessary resources for speed
            page.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico}", lambda route: route.abort())
            page.route("**/*.{css,woff,woff2,ttf,eot}", lambda route: route.abort())

            response = page.goto(url, wait_until="domcontentloaded")

            # Wait for dynamic content to load
            try:
                page.wait_for_load_state(wait_for, timeout=min(timeout, 15000))
            except Exception:
                pass  # Continue with what we have

            # Scroll to trigger lazy-loaded content
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            page.wait_for_timeout(500)

            html = page.content()
            status = response.status if response else 0
            final_url = page.url

            browser.close()

            return {
                "html": html,
                "status_code": status,
                "final_url": final_url,
            }

    except Exception as e:
        logger.warning(f"Browser fetch failed for {url}: {e}")
        return None


def fetch_with_browser_async(
    url: str,
    timeout: int = 30000,
    user_agent: Optional[str] = None,
) -> Optional[dict]:
    """
    Async-compatible browser fetch (runs in sync but designed for thread pool use).
    """
    return fetch_with_browser(url, timeout=timeout, user_agent=user_agent)


# JS-heavy gaming sites that need browser rendering
JS_HEAVY_DOMAINS = {
    "polygon.com",
    "theverge.com",
    "wired.com",
    "gamesradar.com",
    "techradar.com",
    "denofgeek.com",
    "cbr.com",
    "screenrant.com",
}


def needs_browser(url: str, response_text: str = "") -> bool:
    """
    Determine if a URL likely needs browser rendering.

    Checks domain list and content heuristics (empty body, React/Angular markers).
    """
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower().removeprefix("www.")

    if domain in JS_HEAVY_DOMAINS:
        return True

    if response_text:
        # Detect SPA shells with no real content
        indicators = [
            '<div id="root"></div>',
            '<div id="app"></div>',
            '<div id="__next"></div>',
            "window.__INITIAL_STATE__",
            "window.__NUXT__",
        ]
        text_len = len(response_text.strip())
        body_text = ""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response_text, "html.parser")
            body = soup.find("body")
            if body:
                body_text = body.get_text(strip=True)
        except Exception:
            pass

        # Very little text content despite having HTML
        if text_len > 1000 and len(body_text) < 200:
            return True

        for indicator in indicators:
            if indicator in response_text and len(body_text) < 500:
                return True

    return False
