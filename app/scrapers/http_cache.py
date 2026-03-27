"""
HTTP conditional request support (ETag / Last-Modified).

Saves bandwidth and avoids re-downloading unchanged pages.
Stores cache entries in the database via outlet.scraper_config.
"""
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def conditional_get(
    url: str,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
    headers: Optional[dict] = None,
    timeout: int = 20,
) -> tuple[Optional[requests.Response], dict]:
    """
    Perform a conditional HTTP GET.

    Returns (response, cache_meta) where:
    - response is None if the content hasn't changed (304)
    - cache_meta contains the new ETag/Last-Modified to store

    Usage:
        resp, meta = conditional_get(url, etag=old_etag, last_modified=old_lm)
        if resp is None:
            # Not modified, skip processing
        else:
            # New content, process resp.text
            # Store meta["etag"] and meta["last_modified"] for next time
    """
    req_headers = dict(headers or {})

    if etag:
        req_headers["If-None-Match"] = etag
    if last_modified:
        req_headers["If-Modified-Since"] = last_modified

    response = requests.get(url, headers=req_headers, timeout=timeout, allow_redirects=True)

    cache_meta = {
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified"),
    }

    if response.status_code == 304:
        logger.debug(f"Not modified (304): {url}")
        return None, cache_meta

    response.raise_for_status()
    return response, cache_meta
