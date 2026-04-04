"""
Campaign Analytics Engine — deep insights beyond basic stats.

Provides send time analysis, segment engagement, campaign comparison,
funnel analysis, top responders, and performance trends.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.campaign import Campaign, OutreachRecord
from app.models.streamer import Streamer
from app.models.investor import GamingInvestor
from app.models.outlet import GamingOutlet

logger = logging.getLogger(__name__)

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_send_time_analysis(db: Session, company_id: int = None) -> dict:
    """Analyze best send times based on open/click patterns."""
    q = db.query(OutreachRecord).filter(
        OutreachRecord.sent_at.isnot(None),
    )
    records = q.all()

    hourly = defaultdict(lambda: {"sent": 0, "opens": 0, "clicks": 0})
    daily = defaultdict(lambda: {"sent": 0, "opens": 0, "clicks": 0})

    for r in records:
        if not r.sent_at:
            continue
        hour = r.sent_at.hour
        day = DAYS_OF_WEEK[r.sent_at.weekday()]
        hourly[hour]["sent"] += 1
        daily[day]["sent"] += 1
        if r.opened_at:
            hourly[hour]["opens"] += 1
            daily[day]["opens"] += 1
        if r.clicked_at:
            hourly[hour]["clicks"] += 1
            daily[day]["clicks"] += 1

    # Find best hour and day by open rate
    best_hour = max(hourly.keys(), key=lambda h: hourly[h]["opens"] / max(hourly[h]["sent"], 1), default=None)
    best_day = max(daily.keys(), key=lambda d: daily[d]["opens"] / max(daily[d]["sent"], 1), default=None)

    return {
        "best_hour": best_hour,
        "best_day": best_day,
        "hourly_rates": dict(hourly),
        "daily_rates": dict(daily),
    }


def get_engagement_by_segment(db: Session, campaign_id: int = None) -> dict:
    """Break down engagement by tier, platform, region, and target type."""
    q = db.query(OutreachRecord).filter(OutreachRecord.sent_at.isnot(None))
    if campaign_id:
        q = q.filter(OutreachRecord.campaign_id == campaign_id)
    records = q.all()

    # Build lookup maps for streamers
    streamer_ids = [r.target_id for r in records if r.target_type == "streamer"]
    streamers = {}
    if streamer_ids:
        for s in db.query(Streamer).filter(Streamer.id.in_(streamer_ids)).all():
            streamers[s.id] = s

    by_tier = defaultdict(lambda: {"sent": 0, "opens": 0, "clicks": 0, "replies": 0})
    by_platform = defaultdict(lambda: {"sent": 0, "opens": 0, "clicks": 0, "replies": 0})
    by_region = defaultdict(lambda: {"sent": 0, "opens": 0, "clicks": 0, "replies": 0})
    by_type = defaultdict(lambda: {"sent": 0, "opens": 0, "clicks": 0, "replies": 0})

    for r in records:
        by_type[r.target_type]["sent"] += 1
        if r.opened_at:
            by_type[r.target_type]["opens"] += 1
        if r.clicked_at:
            by_type[r.target_type]["clicks"] += 1
        if r.replied_at:
            by_type[r.target_type]["replies"] += 1

        if r.target_type == "streamer" and r.target_id in streamers:
            s = streamers[r.target_id]
            tier = getattr(s, "influence_tier", "unknown") or "unknown"
            plat = s.primary_platform or "unknown"
            region = getattr(s, "region", "unknown") or "unknown"

            for bucket, key in [(by_tier, tier), (by_platform, plat), (by_region, region)]:
                bucket[key]["sent"] += 1
                if r.opened_at:
                    bucket[key]["opens"] += 1
                if r.clicked_at:
                    bucket[key]["clicks"] += 1
                if r.replied_at:
                    bucket[key]["replies"] += 1

    def add_rates(d):
        for k, v in d.items():
            s = max(v["sent"], 1)
            v["open_rate"] = round(v["opens"] / s * 100, 1)
            v["click_rate"] = round(v["clicks"] / s * 100, 1)
            v["reply_rate"] = round(v["replies"] / s * 100, 1)
        return dict(d)

    return {
        "by_tier": add_rates(by_tier),
        "by_platform": add_rates(by_platform),
        "by_region": add_rates(by_region),
        "by_type": add_rates(by_type),
    }


def compare_campaigns(db: Session, campaign_ids: list[int]) -> list[dict]:
    """Side-by-side comparison of multiple campaigns."""
    campaigns = db.query(Campaign).filter(Campaign.id.in_(campaign_ids)).all()
    result = []
    for c in campaigns:
        sent = max(c.sent_count or 0, 1)
        result.append({
            "id": c.id,
            "name": c.name,
            "total_targets": c.total_targets or 0,
            "sent": c.sent_count or 0,
            "open_rate": round((c.opened_count or 0) / sent * 100, 1),
            "click_rate": round((c.clicked_count or 0) / sent * 100, 1),
            "reply_rate": round((c.replied_count or 0) / sent * 100, 1),
            "bounce_rate": round((c.bounced_count or 0) / sent * 100, 1),
        })
    return result


def get_funnel_analysis(db: Session, campaign_id: int) -> dict:
    """Step-by-step dropoff funnel for a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    total = campaign.total_targets or 0
    personalized = campaign.personalized_count or 0
    sent = campaign.sent_count or 0
    delivered = campaign.delivered_count or 0
    opened = campaign.opened_count or 0
    clicked = campaign.clicked_count or 0
    replied = campaign.replied_count or 0

    def step(name, count, prev):
        rate = round(count / max(total, 1) * 100, 1)
        dropoff = round((prev - count) / max(prev, 1) * 100, 1) if prev > 0 else 0
        return {"name": name, "count": count, "rate": rate, "dropoff": dropoff}

    steps = [
        step("Total Targets", total, total),
        step("Personalized", personalized, total),
        step("Sent", sent, personalized),
        step("Delivered", delivered, sent),
        step("Opened", opened, delivered),
        step("Clicked", clicked, opened),
        step("Replied", replied, clicked),
    ]

    return {"campaign_id": campaign.id, "campaign_name": campaign.name, "steps": steps}


def get_top_responders(db: Session, limit: int = 20) -> list[dict]:
    """Contacts with highest response rates across all campaigns."""
    records = db.query(OutreachRecord).filter(OutreachRecord.sent_at.isnot(None)).all()

    by_contact = defaultdict(lambda: {"name": "", "type": "", "sent": 0, "opens": 0, "clicks": 0, "replies": 0})
    for r in records:
        key = f"{r.target_type}:{r.target_id}"
        by_contact[key]["name"] = r.target_name
        by_contact[key]["type"] = r.target_type
        by_contact[key]["id"] = r.target_id
        by_contact[key]["sent"] += 1
        if r.opened_at:
            by_contact[key]["opens"] += 1
        if r.clicked_at:
            by_contact[key]["clicks"] += 1
        if r.replied_at:
            by_contact[key]["replies"] += 1

    # Sort by reply rate then open rate
    ranked = sorted(
        by_contact.values(),
        key=lambda x: (x["replies"] / max(x["sent"], 1), x["opens"] / max(x["sent"], 1)),
        reverse=True,
    )[:limit]

    result = []
    for c in ranked:
        sent = max(c["sent"], 1)
        result.append({
            "contact_type": c["type"],
            "contact_id": c.get("id", 0),
            "contact_name": c["name"],
            "total_received": c["sent"],
            "opens": c["opens"],
            "clicks": c["clicks"],
            "replies": c["replies"],
            "open_rate": round(c["opens"] / sent * 100, 1),
            "reply_rate": round(c["replies"] / sent * 100, 1),
        })
    return result


def get_performance_trends(db: Session, days: int = 90) -> list[dict]:
    """Weekly performance trends."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    records = (
        db.query(OutreachRecord)
        .filter(OutreachRecord.sent_at >= cutoff)
        .all()
    )

    by_week = defaultdict(lambda: {"sent": 0, "opens": 0, "clicks": 0, "replies": 0})
    for r in records:
        if not r.sent_at:
            continue
        week = r.sent_at.strftime("%Y-W%W")
        by_week[week]["sent"] += 1
        if r.opened_at:
            by_week[week]["opens"] += 1
        if r.clicked_at:
            by_week[week]["clicks"] += 1
        if r.replied_at:
            by_week[week]["replies"] += 1

    periods = []
    for week in sorted(by_week.keys()):
        d = by_week[week]
        sent = max(d["sent"], 1)
        periods.append({
            "period": week,
            "sent": d["sent"],
            "open_rate": round(d["opens"] / sent * 100, 1),
            "click_rate": round(d["clicks"] / sent * 100, 1),
            "reply_rate": round(d["replies"] / sent * 100, 1),
        })
    return periods


def get_analytics_summary(db: Session) -> dict:
    """High-level analytics summary across all campaigns."""
    campaigns = db.query(Campaign).filter(Campaign.status != "draft").all()
    total_sent = sum(c.sent_count or 0 for c in campaigns)
    total_opened = sum(c.opened_count or 0 for c in campaigns)
    total_clicked = sum(c.clicked_count or 0 for c in campaigns)
    total_replied = sum(c.replied_count or 0 for c in campaigns)
    sent = max(total_sent, 1)

    best_campaign = max(
        campaigns,
        key=lambda c: (c.replied_count or 0) / max(c.sent_count or 0, 1),
        default=None,
    )

    top = get_top_responders(db, limit=1)

    return {
        "total_campaigns": len(campaigns),
        "total_sent": total_sent,
        "overall_open_rate": round(total_opened / sent * 100, 1),
        "overall_click_rate": round(total_clicked / sent * 100, 1),
        "overall_reply_rate": round(total_replied / sent * 100, 1),
        "best_performing_campaign": best_campaign.name if best_campaign else None,
        "top_responder_name": top[0]["contact_name"] if top else None,
    }
