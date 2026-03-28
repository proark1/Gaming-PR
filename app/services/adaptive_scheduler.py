"""
Smart adaptive scheduling for outlet scraping.

Outlets that publish frequently get scraped more often.
Outlets that rarely publish get scraped less.
Failed outlets get progressively longer delays.
"""
import logging
import math
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.models.outlet import GamingOutlet

logger = logging.getLogger(__name__)

# Scrape interval bounds (minutes)
MIN_INTERVAL = 10
MAX_INTERVAL = 360  # 6 hours
DEFAULT_INTERVAL = 30


def calculate_scrape_interval(outlet: GamingOutlet) -> int:
    """
    Calculate the optimal scrape interval for an outlet (in minutes).

    Based on:
    - Average articles per scrape (more articles = scrape more often)
    - Consecutive failures (more failures = longer delay)
    - Priority (higher priority = scrape more often)
    - Time since last successful scrape
    """
    # Base interval from priority
    priority = outlet.priority or 5
    base = DEFAULT_INTERVAL * (priority / 5)  # Priority 1 = 6min, 5 = 30min, 10 = 60min

    # Adjust for article frequency
    avg = outlet.avg_articles_per_scrape or 0
    if avg > 10:
        base *= 0.5   # High-volume: scrape twice as often
    elif avg > 5:
        base *= 0.75  # Medium-volume
    elif avg < 1 and outlet.total_articles_scraped and outlet.total_articles_scraped > 0:
        base *= 2.0   # Low-volume: scrape less often

    # Penalty for failures (exponential backoff)
    failures = outlet.consecutive_failures or 0
    if failures > 0:
        penalty = min(2 ** failures, 12)  # Cap at 12x multiplier
        base *= penalty

    # Clamp to bounds
    interval = max(MIN_INTERVAL, min(int(base), MAX_INTERVAL))

    return interval


def get_outlets_due_for_scrape(db: Session) -> list[GamingOutlet]:
    """
    Get all active outlets that are due for their next scrape.

    Returns outlets sorted by priority (highest first).
    """
    now = datetime.now(timezone.utc)
    outlets = (
        db.query(GamingOutlet)
        .filter(GamingOutlet.is_active == True)
        .order_by(GamingOutlet.priority.asc())
        .all()
    )

    due = []
    for outlet in outlets:
        interval = calculate_scrape_interval(outlet)

        if not outlet.last_scraped_at:
            due.append(outlet)
            continue

        last = outlet.last_scraped_at.replace(tzinfo=timezone.utc) if outlet.last_scraped_at.tzinfo is None else outlet.last_scraped_at
        next_scrape = last + timedelta(minutes=interval)
        if now >= next_scrape:
            due.append(outlet)

    logger.info(f"Adaptive scheduler: {len(due)}/{len(outlets)} outlets due for scrape")
    return due


def get_schedule_info(db: Session) -> list[dict]:
    """Get scheduling info for all outlets (for monitoring dashboard)."""
    now = datetime.now(timezone.utc)
    outlets = (
        db.query(GamingOutlet)
        .filter(GamingOutlet.is_active == True)
        .order_by(GamingOutlet.priority.asc())
        .all()
    )

    info = []
    for outlet in outlets:
        interval = calculate_scrape_interval(outlet)
        last = outlet.last_scraped_at
        if last and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        next_scrape = last + timedelta(minutes=interval) if last else now

        info.append({
            "outlet_id": outlet.id,
            "name": outlet.name,
            "priority": outlet.priority,
            "interval_minutes": interval,
            "avg_articles_per_scrape": outlet.avg_articles_per_scrape,
            "consecutive_failures": outlet.consecutive_failures,
            "last_scraped_at": last.isoformat() if last else None,
            "next_scrape_at": next_scrape.isoformat(),
            "is_overdue": now >= next_scrape,
        })

    return info
