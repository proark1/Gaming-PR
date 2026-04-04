"""
Influencer scoring, ranking, and daily snapshot service.

Computes engagement rate, influence score, tier, and estimated sponsorship costs.
"""
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.streamer import Streamer
from app.models.streamer_snapshot import StreamerSnapshot

logger = logging.getLogger(__name__)

# Platform CPM baselines (USD per 1000 viewers)
PLATFORM_CPM = {
    "twitch": 3.50,
    "youtube": 5.00,
    "kick": 2.50,
    "rumble": 2.00,
    "tiktok": 4.00,
}

# Sponsorship rate multipliers per platform (per stream/video)
PLATFORM_SPONSOR_MULT = {
    "twitch": 0.05,   # $50 per 1000 avg viewers per stream
    "youtube": 0.08,  # $80 per 1000 subscribers per video
    "kick": 0.03,
    "rumble": 0.02,
    "tiktok": 0.04,
}

TIER_THRESHOLDS = [
    (80, "diamond"),
    (60, "platinum"),
    (40, "gold"),
    (20, "silver"),
    (0, "bronze"),
]


def compute_engagement_rate(streamer: Streamer) -> float:
    """Compute engagement rate = avg_viewers / followers (0.0-1.0)."""
    viewers = streamer.twitch_avg_viewers or 0
    followers = streamer.total_followers or 0
    if followers == 0:
        return 0.0
    return min(round(viewers / followers, 4), 1.0)


def _count_platforms(streamer: Streamer) -> int:
    """Count how many platforms a streamer is active on."""
    count = 0
    if streamer.twitch_username:
        count += 1
    if streamer.youtube_channel_id:
        count += 1
    if streamer.x_username:
        count += 1
    if streamer.kick_username:
        count += 1
    if streamer.rumble_channel_id:
        count += 1
    if streamer.tiktok_username:
        count += 1
    if streamer.instagram_username:
        count += 1
    return count


def compute_influence_score(streamer: Streamer) -> float:
    """
    Compute composite influence score (0-100).

    Weights:
    - Engagement rate: 30%
    - Follower reach (log scale): 25%
    - Platform diversity: 15%
    - Verification/partner status: 15%
    - Content diversity: 15%
    """
    # Engagement (0-30): engagement rate normalized
    engagement = compute_engagement_rate(streamer)
    # Typical top engagement is ~10%, so scale accordingly
    engagement_score = min(engagement / 0.10, 1.0) * 30

    # Follower reach (0-25): log scale, 1M followers = 25
    followers = streamer.total_followers or 0
    if followers > 0:
        reach_score = min(math.log10(followers) / 6.0, 1.0) * 25  # 1M = log10(1M) = 6
    else:
        reach_score = 0

    # Platform diversity (0-15): more platforms = higher
    platform_count = _count_platforms(streamer)
    diversity_score = min(platform_count / 4.0, 1.0) * 15

    # Verification (0-15): partner/verified status
    verification_score = 0
    if streamer.twitch_is_partner:
        verification_score += 7
    elif streamer.twitch_is_affiliate:
        verification_score += 4
    if streamer.is_verified:
        verification_score += 5
    if getattr(streamer, "kick_is_verified", False):
        verification_score += 3
    verification_score = min(verification_score, 15)

    # Content diversity (0-15): more content types = higher
    content_types = streamer.content_types or []
    game_focus = streamer.game_focus or []
    content_score = min((len(content_types) + len(game_focus)) / 8.0, 1.0) * 15

    total = engagement_score + reach_score + diversity_score + verification_score + content_score
    return round(min(total, 100.0), 1)


def assign_tier(score: float) -> str:
    """Map influence score to tier name."""
    for threshold, tier in TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return "bronze"


def estimate_cpm(streamer: Streamer) -> float:
    """Estimate CPM (cost per 1000 impressions) in USD."""
    platform = (streamer.primary_platform or "twitch").lower()
    base_cpm = PLATFORM_CPM.get(platform, 3.0)
    engagement = compute_engagement_rate(streamer)

    # Higher engagement = premium CPM (up to 3x base)
    multiplier = 1.0 + min(engagement / 0.05, 2.0)
    return round(base_cpm * multiplier, 2)


def estimate_sponsorship_rate(streamer: Streamer) -> float:
    """Estimate per-stream/video sponsorship cost in USD."""
    platform = (streamer.primary_platform or "twitch").lower()
    mult = PLATFORM_SPONSOR_MULT.get(platform, 0.05)

    if platform == "youtube":
        base = streamer.youtube_subscribers or 0
    else:
        base = streamer.twitch_avg_viewers or streamer.kick_avg_viewers or 0

    rate = base * mult
    # Minimum $25 for any sponsored content
    return round(max(rate, 25.0), 0)


def score_streamer(streamer: Streamer) -> dict:
    """Compute all scoring metrics for a single streamer."""
    engagement = compute_engagement_rate(streamer)
    score = compute_influence_score(streamer)
    tier = assign_tier(score)
    cpm = estimate_cpm(streamer)
    sponsor_rate = estimate_sponsorship_rate(streamer)
    platform_count = _count_platforms(streamer)

    return {
        "engagement_rate": engagement,
        "influence_score": score,
        "influence_tier": tier,
        "estimated_cpm_usd": cpm,
        "sponsorship_rate_usd": sponsor_rate,
        "platform_count": platform_count,
    }


def score_all_streamers(db: Session) -> int:
    """Recompute scores for all active streamers. Returns count updated."""
    streamers = db.query(Streamer).filter(Streamer.is_active.is_(True)).all()
    count = 0
    for s in streamers:
        metrics = score_streamer(s)
        s.engagement_rate = metrics["engagement_rate"]
        s.influence_score = metrics["influence_score"]
        s.influence_tier = metrics["influence_tier"]
        s.estimated_cpm_usd = metrics["estimated_cpm_usd"]
        s.sponsorship_rate_usd = metrics["sponsorship_rate_usd"]
        s.platform_count = metrics["platform_count"]
        count += 1

    db.commit()
    logger.info("Scored %d streamers", count)
    return count


def capture_daily_snapshot(db: Session) -> int:
    """Capture metric snapshots for all active streamers. Returns count."""
    streamers = db.query(Streamer).filter(Streamer.is_active.is_(True)).all()
    count = 0
    for s in streamers:
        snapshot = StreamerSnapshot(
            streamer_id=s.id,
            total_followers=s.total_followers,
            twitch_followers=s.twitch_followers,
            youtube_subscribers=s.youtube_subscribers,
            kick_followers=s.kick_followers,
            twitch_avg_viewers=s.twitch_avg_viewers,
            engagement_rate=s.engagement_rate,
            influence_score=s.influence_score,
        )
        db.add(snapshot)
        count += 1

    db.commit()
    logger.info("Captured %d streamer snapshots", count)
    return count


def get_growth_trend(
    db: Session, streamer_id: int, days: int = 30,
) -> dict:
    """Calculate follower growth over a period."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    snapshots = (
        db.query(StreamerSnapshot)
        .filter(
            StreamerSnapshot.streamer_id == streamer_id,
            StreamerSnapshot.captured_at >= cutoff,
        )
        .order_by(StreamerSnapshot.captured_at)
        .all()
    )

    if len(snapshots) < 2:
        return {"days": days, "snapshots": len(snapshots), "growth_pct": 0, "trend": "insufficient_data"}

    first = snapshots[0].total_followers or 0
    last = snapshots[-1].total_followers or 0

    if first == 0:
        growth_pct = 0
    else:
        growth_pct = round(((last - first) / first) * 100, 2)

    trend = "growing" if growth_pct > 1 else ("declining" if growth_pct < -1 else "stable")

    return {
        "days": days,
        "snapshots": len(snapshots),
        "followers_start": first,
        "followers_end": last,
        "growth_pct": growth_pct,
        "trend": trend,
        "history": [
            {"date": s.captured_at.isoformat(), "followers": s.total_followers, "score": s.influence_score}
            for s in snapshots
        ],
    }


# APScheduler job
def daily_score_and_snapshot_job():
    """APScheduler job: score all streamers and capture daily snapshot."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        score_all_streamers(db)
        capture_daily_snapshot(db)
    except Exception as exc:
        logger.error("Daily scoring/snapshot failed: %s", exc)
    finally:
        db.close()
