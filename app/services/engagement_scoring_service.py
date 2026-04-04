"""
Contact Engagement Scoring — learns from outreach history to improve matching.

Computes per-contact engagement scores from OutreachRecord data.
Contacts who open, click, and reply get higher scores; unresponsive ones get lower.
Used by matching_service to weight recommendations.
"""
import logging
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.campaign import OutreachRecord
from app.models.contact_engagement import ContactEngagementScore

logger = logging.getLogger(__name__)


def compute_engagement_scores(db: Session) -> int:
    """Compute engagement scores for all contacts from OutreachRecord data."""
    records = db.query(OutreachRecord).filter(OutreachRecord.sent_at.isnot(None)).all()

    by_contact: dict[str, dict] = defaultdict(lambda: {
        "sent": 0, "opens": 0, "clicks": 0, "replies": 0,
        "response_times": [],
    })

    for r in records:
        key = f"{r.target_type}:{r.target_id}"
        by_contact[key]["type"] = r.target_type
        by_contact[key]["id"] = r.target_id
        by_contact[key]["sent"] += 1
        if r.opened_at:
            by_contact[key]["opens"] += 1
            if r.sent_at:
                hours = (r.opened_at - r.sent_at).total_seconds() / 3600
                by_contact[key]["response_times"].append(hours)
        if r.clicked_at:
            by_contact[key]["clicks"] += 1
        if r.replied_at:
            by_contact[key]["replies"] += 1

    updated = 0
    now = datetime.now(timezone.utc)

    for key, data in by_contact.items():
        contact_type = data.get("type")
        contact_id = data.get("id")
        if not contact_type or not contact_id:
            continue

        sent = max(data["sent"], 1)
        open_rate = data["opens"] / sent
        click_rate = data["clicks"] / sent
        reply_rate = data["replies"] / sent
        avg_resp = (
            sum(data["response_times"]) / len(data["response_times"])
            if data["response_times"] else None
        )

        # Score: open_rate*30 + click_rate*30 + reply_rate*40, normalized to 0-100
        raw_score = (open_rate * 30 + click_rate * 30 + reply_rate * 40)
        engagement_score = min(round(raw_score, 1), 100.0)

        # Upsert
        existing = (
            db.query(ContactEngagementScore)
            .filter(
                ContactEngagementScore.contact_type == contact_type,
                ContactEngagementScore.contact_id == contact_id,
            )
            .first()
        )
        if existing:
            existing.total_emails_received = data["sent"]
            existing.total_opens = data["opens"]
            existing.total_clicks = data["clicks"]
            existing.total_replies = data["replies"]
            existing.open_rate = round(open_rate, 4)
            existing.click_rate = round(click_rate, 4)
            existing.reply_rate = round(reply_rate, 4)
            existing.avg_response_time_hours = round(avg_resp, 1) if avg_resp else None
            existing.engagement_score = engagement_score
            existing.last_computed_at = now
        else:
            score = ContactEngagementScore(
                contact_type=contact_type,
                contact_id=contact_id,
                total_emails_received=data["sent"],
                total_opens=data["opens"],
                total_clicks=data["clicks"],
                total_replies=data["replies"],
                open_rate=round(open_rate, 4),
                click_rate=round(click_rate, 4),
                reply_rate=round(reply_rate, 4),
                avg_response_time_hours=round(avg_resp, 1) if avg_resp else None,
                engagement_score=engagement_score,
                last_computed_at=now,
            )
            db.add(score)
        updated += 1

    db.commit()
    logger.info("Updated engagement scores for %d contacts", updated)
    return updated


def get_engagement_score(db: Session, contact_type: str, contact_id: int) -> float:
    """Get a contact's engagement score. Returns 50.0 (neutral) if no data."""
    score = (
        db.query(ContactEngagementScore)
        .filter(
            ContactEngagementScore.contact_type == contact_type,
            ContactEngagementScore.contact_id == contact_id,
        )
        .first()
    )
    return score.engagement_score if score else 50.0


def compute_engagement_scores_job():
    """APScheduler entry point."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        compute_engagement_scores(db)
    except Exception as exc:
        logger.error("Engagement scoring job failed: %s", exc)
    finally:
        db.close()
