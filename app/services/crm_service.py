"""
Contact Relationship Management (CRM) service.

Tracks all interactions with contacts, manages relationship stages,
and provides pipeline overview for outreach management.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.activity import ContactActivity
from app.models.investor import GamingInvestor
from app.models.outlet import GamingOutlet
from app.models.streamer import Streamer

logger = logging.getLogger(__name__)

VALID_STAGES = ["new", "contacted", "responded", "negotiating", "partner", "inactive"]

# Model lookup by contact type
_MODELS = {
    "streamer": Streamer,
    "outlet": GamingOutlet,
    "vc": GamingInvestor,
}


def log_activity(
    db: Session,
    contact_type: str,
    contact_id: int,
    activity_type: str,
    details: Optional[dict] = None,
    created_by: Optional[int] = None,
) -> ContactActivity:
    """Record an interaction with a contact."""
    activity = ContactActivity(
        contact_type=contact_type,
        contact_id=contact_id,
        activity_type=activity_type,
        details=details,
        created_by=created_by,
    )
    db.add(activity)

    # Update contact's last_contacted_at and total_outreach_count
    model = _MODELS.get(contact_type)
    if model and activity_type == "email_sent":
        entity = db.query(model).filter(model.id == contact_id).first()
        if entity and hasattr(entity, "last_contacted_at"):
            entity.last_contacted_at = datetime.now(timezone.utc)
            entity.total_outreach_count = (entity.total_outreach_count or 0) + 1

    db.commit()
    db.refresh(activity)
    return activity


def get_timeline(
    db: Session,
    contact_type: str,
    contact_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[ContactActivity]:
    """Full interaction history for a contact."""
    return (
        db.query(ContactActivity)
        .filter(
            ContactActivity.contact_type == contact_type,
            ContactActivity.contact_id == contact_id,
        )
        .order_by(ContactActivity.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_relationship_stage(
    db: Session,
    contact_type: str,
    contact_id: int,
    new_stage: str,
    user_id: Optional[int] = None,
) -> str:
    """Change a contact's relationship stage and log the change."""
    if new_stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage: {new_stage}. Must be one of: {VALID_STAGES}")

    model = _MODELS.get(contact_type)
    if not model:
        raise ValueError(f"Unknown contact type: {contact_type}")

    entity = db.query(model).filter(model.id == contact_id).first()
    if not entity:
        raise ValueError(f"{contact_type} {contact_id} not found")

    old_stage = getattr(entity, "relationship_stage", "new") or "new"
    entity.relationship_stage = new_stage

    log_activity(
        db, contact_type, contact_id, "stage_changed",
        details={"old_stage": old_stage, "new_stage": new_stage},
        created_by=user_id,
    )

    return new_stage


def add_note(
    db: Session,
    contact_type: str,
    contact_id: int,
    note_text: str,
    user_id: Optional[int] = None,
) -> ContactActivity:
    """Add a manual note to a contact's timeline."""
    return log_activity(
        db, contact_type, contact_id, "note_added",
        details={"note": note_text},
        created_by=user_id,
    )


def get_pipeline_summary(db: Session) -> dict:
    """Pipeline overview: contacts grouped by stage for each type (with id/name)."""
    result = {"streamer": {}, "outlet": {}, "vc": {}}

    for contact_type, model in _MODELS.items():
        if not hasattr(model, "relationship_stage"):
            continue

        contacts = (
            db.query(model)
            .filter(model.is_active.is_(True))
            .all()
        )
        by_stage: dict[str, list] = {}
        for c in contacts:
            stage = getattr(c, "relationship_stage", None) or "new"
            by_stage.setdefault(stage, []).append({
                "id": c.id,
                "name": getattr(c, "name", None) or getattr(c, "outlet_name", "Unknown"),
                "total_outreach_count": getattr(c, "total_outreach_count", 0) or 0,
            })
        result[contact_type] = by_stage

    return result


def get_recent_activity(
    db: Session, limit: int = 50,
) -> list[ContactActivity]:
    """Recent activity feed across all contacts."""
    return (
        db.query(ContactActivity)
        .order_by(ContactActivity.created_at.desc())
        .limit(limit)
        .all()
    )


def auto_update_stages_job():
    """APScheduler job: auto-advance relationship stages based on activity."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        _auto_update_stages(db)
    except Exception as exc:
        logger.error("Auto stage update failed: %s", exc)
    finally:
        db.close()


def _auto_update_stages(db: Session) -> int:
    """
    Auto-advance stages based on outreach activity:
    - new + email_sent → contacted
    - contacted + email_opened → responded
    """
    updated = 0

    for contact_type, model in _MODELS.items():
        if not hasattr(model, "relationship_stage"):
            continue

        # new → contacted (if email was sent)
        new_contacts = (
            db.query(model)
            .filter(
                model.is_active.is_(True),
                model.relationship_stage.in_([None, "new"]),
            )
            .all()
        )
        for entity in new_contacts:
            has_sent = (
                db.query(ContactActivity)
                .filter(
                    ContactActivity.contact_type == contact_type,
                    ContactActivity.contact_id == entity.id,
                    ContactActivity.activity_type == "email_sent",
                )
                .first()
            )
            if has_sent:
                entity.relationship_stage = "contacted"
                updated += 1

        # contacted → responded (if email was opened)
        contacted = (
            db.query(model)
            .filter(
                model.is_active.is_(True),
                model.relationship_stage == "contacted",
            )
            .all()
        )
        for entity in contacted:
            has_open = (
                db.query(ContactActivity)
                .filter(
                    ContactActivity.contact_type == contact_type,
                    ContactActivity.contact_id == entity.id,
                    ContactActivity.activity_type.in_(["email_opened", "email_clicked"]),
                )
                .first()
            )
            if has_open:
                entity.relationship_stage = "responded"
                updated += 1

    db.commit()
    if updated:
        logger.info("Auto-updated %d contact stages", updated)
    return updated
