"""
Circuit breaker pattern for outlet scraping.

Prevents hammering outlets that are consistently failing.
Three states: CLOSED (normal), OPEN (blocking), HALF_OPEN (testing).
"""
import logging
import time
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerEntry:
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    opened_at: float = 0.0
    half_open_successes: int = 0


class CircuitBreaker:
    """
    Per-outlet circuit breaker.

    - CLOSED: Normal. After `failure_threshold` consecutive failures, trips to OPEN.
    - OPEN: All requests blocked. After `recovery_timeout` seconds, moves to HALF_OPEN.
    - HALF_OPEN: Allows `half_open_max_calls` test requests.
      If they succeed, resets to CLOSED. If any fail, back to OPEN.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 300.0,  # 5 minutes
        half_open_max_calls: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._circuits: dict[int, CircuitBreakerEntry] = {}

    def _get_entry(self, outlet_id: int) -> CircuitBreakerEntry:
        if outlet_id not in self._circuits:
            self._circuits[outlet_id] = CircuitBreakerEntry()
        return self._circuits[outlet_id]

    def can_execute(self, outlet_id: int) -> bool:
        """Check if a request to this outlet is allowed."""
        entry = self._get_entry(outlet_id)

        if entry.state == CircuitState.CLOSED:
            return True

        if entry.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if time.monotonic() - entry.opened_at >= self.recovery_timeout:
                entry.state = CircuitState.HALF_OPEN
                entry.half_open_successes = 0
                logger.info(f"Circuit breaker HALF_OPEN for outlet {outlet_id}")
                return True
            return False

        if entry.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self, outlet_id: int):
        """Record a successful request."""
        entry = self._get_entry(outlet_id)
        now = time.monotonic()
        entry.last_success_time = now
        entry.success_count += 1

        if entry.state == CircuitState.HALF_OPEN:
            entry.half_open_successes += 1
            if entry.half_open_successes >= self.half_open_max_calls:
                entry.state = CircuitState.CLOSED
                entry.failure_count = 0
                logger.info(f"Circuit breaker CLOSED for outlet {outlet_id} (recovered)")
        elif entry.state == CircuitState.CLOSED:
            entry.failure_count = 0

    def record_failure(self, outlet_id: int):
        """Record a failed request."""
        entry = self._get_entry(outlet_id)
        now = time.monotonic()
        entry.failure_count += 1
        entry.last_failure_time = now

        if entry.state == CircuitState.HALF_OPEN:
            # Any failure in half-open trips back to open
            entry.state = CircuitState.OPEN
            entry.opened_at = now
            logger.warning(f"Circuit breaker re-OPENED for outlet {outlet_id}")
        elif entry.state == CircuitState.CLOSED:
            if entry.failure_count >= self.failure_threshold:
                entry.state = CircuitState.OPEN
                entry.opened_at = now
                logger.warning(
                    f"Circuit breaker OPENED for outlet {outlet_id} "
                    f"after {entry.failure_count} failures"
                )

    def get_status(self, outlet_id: int) -> dict:
        """Get the current circuit breaker status for an outlet."""
        entry = self._get_entry(outlet_id)
        return {
            "outlet_id": outlet_id,
            "state": entry.state.value,
            "failure_count": entry.failure_count,
            "success_count": entry.success_count,
            "last_failure_time": entry.last_failure_time,
            "last_success_time": entry.last_success_time,
        }

    def get_all_statuses(self) -> list[dict]:
        """Get status of all tracked circuits."""
        return [self.get_status(oid) for oid in self._circuits]

    def reset(self, outlet_id: int):
        """Manually reset a circuit breaker."""
        if outlet_id in self._circuits:
            self._circuits[outlet_id] = CircuitBreakerEntry()
            logger.info(f"Circuit breaker manually reset for outlet {outlet_id}")

    def reset_all(self):
        """Reset all circuit breakers."""
        self._circuits.clear()


# Global instance
circuit_breaker = CircuitBreaker()
