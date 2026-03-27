"""Tests for v4 features: circuit breaker, retry queue, stealth, adaptive scheduling."""
import os
import time

os.environ["DATABASE_URL"] = "sqlite:///./test_gaming_pr.db"

from app.scrapers.circuit_breaker import CircuitBreaker, CircuitState
from app.scrapers.retry_queue import RetryQueue
from app.scrapers.stealth import get_random_user_agent, get_stealth_headers, reset_sessions
from app.scrapers.dedup import compute_simhash, is_duplicate, similarity_score
from app.scrapers.browser import needs_browser, is_playwright_available


# ── Circuit Breaker Tests ──


def test_circuit_breaker_starts_closed():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
    assert cb.can_execute(1) is True
    status = cb.get_status(1)
    assert status["state"] == "closed"


def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
    cb.record_failure(1)
    cb.record_failure(1)
    assert cb.can_execute(1) is True  # Still below threshold
    cb.record_failure(1)
    assert cb.can_execute(1) is False  # Now open
    assert cb.get_status(1)["state"] == "open"


def test_circuit_breaker_success_resets_failures():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure(1)
    cb.record_failure(1)
    cb.record_success(1)
    assert cb.can_execute(1) is True
    assert cb.get_status(1)["failure_count"] == 0


def test_circuit_breaker_half_open_recovery():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, half_open_max_calls=1)
    cb.record_failure(1)
    cb.record_failure(1)
    assert cb.can_execute(1) is False

    time.sleep(0.15)  # Wait for recovery timeout
    assert cb.can_execute(1) is True  # Should be half-open now
    assert cb.get_status(1)["state"] == "half_open"

    cb.record_success(1)
    assert cb.get_status(1)["state"] == "closed"


def test_circuit_breaker_manual_reset():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure(1)
    cb.record_failure(1)
    assert cb.can_execute(1) is False
    cb.reset(1)
    assert cb.can_execute(1) is True


# ── Retry Queue Tests ──


def test_retry_queue_enqueue_and_get():
    rq = RetryQueue()
    rq.enqueue(1, "https://example.com/article1", 10, "timeout")
    assert rq.pending_count == 1
    assert rq.stats["total_enqueued"] == 1


def test_retry_queue_no_duplicates():
    rq = RetryQueue()
    rq.enqueue(1, "https://example.com/article1", 10)
    rq.enqueue(1, "https://example.com/article1", 10)  # Duplicate
    assert rq.pending_count == 1


def test_retry_queue_ready_items_respects_backoff():
    rq = RetryQueue()
    rq.enqueue(1, "https://example.com/article1", 10)
    # Items are not ready immediately (60s backoff)
    ready = rq.get_ready_items()
    assert len(ready) == 0
    assert rq.pending_count == 1


def test_retry_queue_mark_success():
    rq = RetryQueue()
    rq.enqueue(1, "https://example.com/article1", 10)
    # Manually create a ready item
    from app.scrapers.retry_queue import RetryItem
    item = RetryItem(article_id=1, url="https://example.com/article1", outlet_id=10)
    rq.mark_success(item)
    assert rq.stats["total_succeeded"] == 1


def test_retry_queue_exhaustion():
    rq = RetryQueue()
    from app.scrapers.retry_queue import RetryItem
    item = RetryItem(article_id=1, url="https://example.com/x", outlet_id=10, attempt=3, max_attempts=3)
    rq.requeue(item, "still failing")
    assert rq.stats["total_exhausted"] == 1


# ── Stealth Headers Tests ──


def test_get_random_user_agent():
    ua = get_random_user_agent()
    assert isinstance(ua, str)
    assert len(ua) > 50
    assert "Mozilla" in ua


def test_stealth_headers_have_required_fields():
    headers = get_stealth_headers(language="en")
    assert "User-Agent" in headers
    assert "Accept" in headers
    assert "Accept-Language" in headers
    assert "en-US" in headers["Accept-Language"]


def test_stealth_headers_language_match():
    headers = get_stealth_headers(language="ja")
    assert "ja-JP" in headers["Accept-Language"]

    headers = get_stealth_headers(language="es")
    assert "es-ES" in headers["Accept-Language"]


def test_reset_sessions():
    from app.scrapers.stealth import get_session_headers, _domain_sessions
    get_session_headers("example.com")
    assert "example.com" in _domain_sessions
    reset_sessions()
    assert "example.com" not in _domain_sessions


# ── Browser Detection Tests ──


def test_needs_browser_js_heavy_domain():
    assert needs_browser("https://www.polygon.com/article/test") is True
    assert needs_browser("https://www.ign.com/article/test") is False


def test_needs_browser_spa_detection():
    spa_html = '<html><body><div id="root"></div><script src="app.js"></script></body></html>'
    assert needs_browser("https://example.com/article", spa_html) is True

    normal_html = '<html><body><article><p>' + 'Content. ' * 100 + '</p></article></body></html>'
    assert needs_browser("https://example.com/article", normal_html) is False


def test_playwright_availability():
    # Just make sure it doesn't crash
    result = is_playwright_available()
    assert isinstance(result, bool)


# ── Adaptive Scheduler Tests ──


def test_adaptive_scheduler_interval():
    from app.services.adaptive_scheduler import calculate_scrape_interval
    from unittest.mock import MagicMock

    outlet = MagicMock()
    outlet.priority = 5
    outlet.avg_articles_per_scrape = 5
    outlet.consecutive_failures = 0
    outlet.total_articles_scraped = 100

    interval = calculate_scrape_interval(outlet)
    assert 10 <= interval <= 360

    # High priority = shorter interval
    outlet.priority = 1
    high_pri_interval = calculate_scrape_interval(outlet)
    outlet.priority = 10
    low_pri_interval = calculate_scrape_interval(outlet)
    assert high_pri_interval < low_pri_interval

    # Failures increase interval
    outlet.priority = 5
    outlet.consecutive_failures = 0
    healthy_interval = calculate_scrape_interval(outlet)
    outlet.consecutive_failures = 3
    failing_interval = calculate_scrape_interval(outlet)
    assert failing_interval > healthy_interval
