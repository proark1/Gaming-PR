"""
Retry queue for failed article extractions.

Failed content extractions get queued for retry with exponential backoff.
"""
import logging
import threading
import time
from dataclasses import dataclass, field
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RetryItem:
    article_id: int
    url: str
    outlet_id: int
    attempt: int = 0
    max_attempts: int = 3
    next_retry_at: float = 0.0
    last_error: str = ""
    created_at: float = field(default_factory=time.monotonic)


class RetryQueue:
    """
    In-memory retry queue with exponential backoff.

    Backoff schedule: 60s, 300s, 900s (1min, 5min, 15min)
    """

    BACKOFF_SECONDS = [60, 300, 900]

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._lock = threading.Lock()
        self._queue: deque[RetryItem] = deque(maxlen=max_size)
        self._seen_urls: set[str] = set()
        self._lock = threading.Lock()
        self._stats = {
            "total_enqueued": 0,
            "total_retried": 0,
            "total_succeeded": 0,
            "total_exhausted": 0,
        }

    def enqueue(self, article_id: int, url: str, outlet_id: int, error: str = ""):
        """Add a failed article to the retry queue."""
        with self._lock:
            if url in self._seen_urls:
                return  # Already queued

            backoff = self.BACKOFF_SECONDS[0] if self.BACKOFF_SECONDS else 60

            item = RetryItem(
                article_id=article_id,
                url=url,
                outlet_id=outlet_id,
                attempt=1,
                next_retry_at=time.monotonic() + backoff,
                last_error=error,
            )
            self._queue.append(item)
            self._seen_urls.add(url)
            self._stats["total_enqueued"] += 1
            logger.debug(f"Enqueued retry for article {article_id}: {url}")

    def get_ready_items(self) -> list[RetryItem]:
        """Get all items that are ready for retry."""
        with self._lock:
            now = time.monotonic()
            ready = []
            remaining = deque()

            while self._queue:
                item = self._queue.popleft()
                if item.next_retry_at <= now:
                    ready.append(item)
                else:
                    remaining.append(item)

            self._queue = remaining
            return ready

    def requeue(self, item: RetryItem, error: str = ""):
        """Re-queue an item after a failed retry attempt."""
        with self._lock:
            item.attempt += 1
            item.last_error = error

            if item.attempt > item.max_attempts:
                self._seen_urls.discard(item.url)
                self._stats["total_exhausted"] += 1
                logger.warning(f"Retry exhausted for {item.url} after {item.max_attempts} attempts")
                return

            backoff_idx = min(item.attempt - 1, len(self.BACKOFF_SECONDS) - 1)
            backoff = self.BACKOFF_SECONDS[backoff_idx]
            item.next_retry_at = time.monotonic() + backoff

            self._queue.append(item)
            self._stats["total_retried"] += 1

    def mark_success(self, item: RetryItem):
        """Mark a retry as successful."""
        with self._lock:
            self._seen_urls.discard(item.url)
            self._stats["total_succeeded"] += 1
            logger.debug(f"Retry succeeded for {item.url} on attempt {item.attempt}")

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._queue)

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                **self._stats,
                "pending": len(self._queue),
            }

    def clear(self):
        """Clear the queue."""
        with self._lock:
            self._queue.clear()
            self._seen_urls.clear()


# Global instance
retry_queue = RetryQueue()
