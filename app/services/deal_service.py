"""
Deal & Sponsorship Tracker — manage investment deals and streamer sponsorships.

Tracks deals from initial interest through closing, with stage history,
value tracking, and attribution to campaigns/pitches.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.deal import Deal, DealStageHistory

logger = logging.getLogger(__name__)

INVESTMENT_STAGES = ["interested", "due_diligence", "term_sheet", "closing", "closed_won", "closed_lost"]
SPONSORSHIP_STAGES = ["pitched", "negotiating", "contracted", "active", "completed", "cancelled"]
PRESS_STAGES = ["pitched", "interested", "active", "published", "cancelled"]

STAGE_MAP = {
    "investment": INVESTMENT_STAGES,
    "sponsorship": SPONSORSHIP_STAGES,
    "press_partnership": PRESS_STAGES,
    "review": PRESS_STAGES,
}

WON_STAGES = {"closed_won", "completed", "published"}
LOST_STAGES = {"closed_lost", "cancelled"}


def create_deal(db: Session, data: dict, user_id: int = None) -> Deal:
    """Create a new deal."""
    deal_type = data.get("deal_type", "investment")
    valid_stages = STAGE_MAP.get(deal_type, INVESTMENT_STAGES)

    deal = Deal(
        company_id=data["company_id"],
        contact_type=data["contact_type"],
        contact_id=data["contact_id"],
        contact_name=data["contact_name"],
        deal_type=deal_type,
        title=data["title"],
        description=data.get("description"),
        deal_value_usd=data.get("deal_value_usd"),
        payment_terms=data.get("payment_terms"),
        expected_close_date=data.get("expected_close_date"),
        source_campaign_id=data.get("source_campaign_id"),
        source_pitch_id=data.get("source_pitch_id"),
        notes=data.get("notes"),
        stage=valid_stages[0],
        created_by=user_id,
    )
    db.add(deal)
    db.flush()

    # Log initial stage
    history = DealStageHistory(
        deal_id=deal.id,
        from_stage="",
        to_stage=deal.stage,
        changed_by=user_id,
        notes="Deal created",
    )
    db.add(history)

    # Log CRM activity
    try:
        from app.services.crm_service import log_activity
        log_activity(
            db, deal.contact_type, deal.contact_id,
            "deal_created",
            {"deal_id": deal.id, "title": deal.title, "type": deal_type},
            user_id,
        )
    except Exception as e:
        logger.warning("Failed to log CRM activity for deal: %s", e)

    db.commit()
    db.refresh(deal)
    return deal


def change_stage(
    db: Session, deal_id: int, new_stage: str,
    notes: str = None, user_id: int = None,
) -> Deal:
    """Advance a deal to a new stage."""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise ValueError(f"Deal {deal_id} not found")

    valid_stages = STAGE_MAP.get(deal.deal_type, INVESTMENT_STAGES)
    if new_stage not in valid_stages:
        raise ValueError(f"Invalid stage '{new_stage}' for {deal.deal_type}. Valid: {valid_stages}")

    old_stage = deal.stage
    if old_stage == new_stage:
        return deal

    deal.stage = new_stage
    deal.stage_changed_at = datetime.now(timezone.utc)

    if new_stage in WON_STAGES:
        deal.actual_close_date = datetime.now(timezone.utc).date()

    history = DealStageHistory(
        deal_id=deal.id,
        from_stage=old_stage,
        to_stage=new_stage,
        changed_by=user_id,
        notes=notes,
    )
    db.add(history)

    # Log CRM activity
    try:
        from app.services.crm_service import log_activity
        log_activity(
            db, deal.contact_type, deal.contact_id,
            "deal_stage_changed",
            {"deal_id": deal.id, "title": deal.title, "from": old_stage, "to": new_stage},
            user_id,
        )
    except Exception as e:
        logger.warning("Failed to log CRM activity: %s", e)

    db.commit()
    db.refresh(deal)
    return deal


def update_deal(db: Session, deal_id: int, data: dict) -> Deal:
    """Update deal fields."""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise ValueError(f"Deal {deal_id} not found")

    updatable = [
        "title", "description", "deal_value_usd", "payment_terms",
        "expected_close_date", "actual_close_date", "contract_url",
        "pitch_deck_url", "deliverables", "notes",
    ]
    for field in updatable:
        if field in data and data[field] is not None:
            setattr(deal, field, data[field])

    db.commit()
    db.refresh(deal)
    return deal


def get_deal(db: Session, deal_id: int) -> Deal:
    """Get a single deal."""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise ValueError(f"Deal {deal_id} not found")
    return deal


def list_deals(
    db: Session,
    company_id: int = None,
    deal_type: str = None,
    stage: str = None,
    contact_type: str = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Deal]:
    """List deals with filters."""
    q = db.query(Deal)
    if company_id:
        q = q.filter(Deal.company_id == company_id)
    if deal_type:
        q = q.filter(Deal.deal_type == deal_type)
    if stage:
        q = q.filter(Deal.stage == stage)
    if contact_type:
        q = q.filter(Deal.contact_type == contact_type)
    return q.order_by(Deal.updated_at.desc()).offset(offset).limit(limit).all()


def get_stage_history(db: Session, deal_id: int) -> list[DealStageHistory]:
    """Get stage transition history for a deal."""
    return (
        db.query(DealStageHistory)
        .filter(DealStageHistory.deal_id == deal_id)
        .order_by(DealStageHistory.changed_at.desc())
        .all()
    )


def get_pipeline(db: Session, company_id: int = None, deal_type: str = None) -> dict:
    """Pipeline view: deals grouped by stage with totals."""
    q = db.query(Deal)
    if company_id:
        q = q.filter(Deal.company_id == company_id)
    if deal_type:
        q = q.filter(Deal.deal_type == deal_type)
    deals = q.all()

    by_stage = {}
    for d in deals:
        if d.stage not in by_stage:
            by_stage[d.stage] = {"count": 0, "value": 0, "deals": []}
        by_stage[d.stage]["count"] += 1
        by_stage[d.stage]["value"] += d.deal_value_usd or 0
        by_stage[d.stage]["deals"].append({
            "id": d.id,
            "title": d.title,
            "contact_name": d.contact_name,
            "contact_type": d.contact_type,
            "deal_type": d.deal_type,
            "deal_value_usd": d.deal_value_usd,
            "expected_close_date": str(d.expected_close_date) if d.expected_close_date else None,
        })

    return by_stage


def get_deal_summary(db: Session, company_id: int = None) -> dict:
    """Aggregate deal statistics."""
    q = db.query(Deal)
    if company_id:
        q = q.filter(Deal.company_id == company_id)
    deals = q.all()

    total = len(deals)
    total_value = sum(d.deal_value_usd or 0 for d in deals)
    won = sum(1 for d in deals if d.stage in WON_STAGES)
    lost = sum(1 for d in deals if d.stage in LOST_STAGES)
    closed = won + lost

    return {
        "total_deals": total,
        "total_value": total_value,
        "by_stage": {},
        "won_count": won,
        "lost_count": lost,
        "win_rate": round(won / max(closed, 1) * 100, 1),
    }


def delete_deal(db: Session, deal_id: int) -> bool:
    """Delete a deal and its history."""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        return False
    db.query(DealStageHistory).filter(DealStageHistory.deal_id == deal_id).delete()
    db.delete(deal)
    db.commit()
    return True
