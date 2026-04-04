"""
Campaign orchestration service.

Ties together message personalization, translation, and email sending
into an automated pipeline with staggered delivery and follow-up support.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models.campaign import Campaign, OutreachRecord, DoNotContact
from app.models.email import ConnectedDomain, SentEmail
from app.models.investor import GamingInvestor
from app.models.message import Message
from app.models.outlet import GamingOutlet
from app.models.personalization import MessagePersonalization
from app.models.streamer import Streamer
from app.services import email_service
from app.services.personalization_service import (
    personalize_and_translate,
)
from app.services.profile_service import (
    compile_investor_profile,
    compile_outlet_profile,
    compile_streamer_profile,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Campaign CRUD
# ---------------------------------------------------------------------------

def create_campaign(db: Session, data: dict) -> Campaign:
    """Create a new campaign in draft status."""
    filters = data.pop("target_filters", None)
    if filters and hasattr(filters, "model_dump"):
        filters = filters.model_dump(exclude_none=True)

    campaign = Campaign(
        status="draft",
        target_filters=filters,
        **data,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def update_campaign(db: Session, campaign_id: int, data: dict) -> Campaign:
    """Update a campaign (only allowed in draft status)."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")
    if campaign.status != "draft":
        raise ValueError(f"Cannot update campaign in '{campaign.status}' status")

    filters = data.pop("target_filters", None)
    if filters is not None:
        if hasattr(filters, "model_dump"):
            filters = filters.model_dump(exclude_none=True)
        campaign.target_filters = filters

    for key, value in data.items():
        if value is not None and hasattr(campaign, key):
            setattr(campaign, key, value)

    db.commit()
    db.refresh(campaign)
    return campaign


def delete_campaign(db: Session, campaign_id: int) -> bool:
    """Delete a campaign (only allowed in draft status)."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return False
    if campaign.status != "draft":
        raise ValueError(f"Cannot delete campaign in '{campaign.status}' status")
    db.delete(campaign)
    db.commit()
    return True


def get_campaign(db: Session, campaign_id: int) -> Optional[Campaign]:
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()


def list_campaigns(
    db: Session,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Campaign]:
    q = db.query(Campaign)
    if status:
        q = q.filter(Campaign.status == status)
    return q.order_by(Campaign.created_at.desc()).offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------

def _resolve_email(entity, target_type: str) -> Optional[str]:
    """Get the best email address for a contact."""
    if target_type == "streamer":
        return entity.contact_email or getattr(entity, "agent_email", None)
    elif target_type == "outlet":
        return entity.contact_email
    elif target_type == "vc":
        return entity.contact_email
    return None


def _apply_filters(entities: list, filters: dict, target_type: str) -> list:
    """Apply filter criteria to a list of entities (Python-side for SQLite compat)."""
    if not filters:
        return entities

    result = []
    for e in entities:
        # Follower filters (streamers only)
        if target_type == "streamer":
            followers = e.total_followers or 0
            if filters.get("min_followers") and followers < filters["min_followers"]:
                continue
            if filters.get("max_followers") and followers > filters["max_followers"]:
                continue
            # Platform filter
            if filters.get("platforms"):
                platform = (e.primary_platform or "").lower()
                if platform not in [p.lower() for p in filters["platforms"]]:
                    continue
            # Game focus filter
            if filters.get("game_focus"):
                entity_games = e.game_focus or []
                if not any(g in entity_games for g in filters["game_focus"]):
                    continue

        # Outlet-specific filters
        if target_type == "outlet":
            if filters.get("outlet_categories"):
                if (e.category or "") not in filters["outlet_categories"]:
                    continue
            if filters.get("outlet_min_priority") and (e.priority or 10) < filters["outlet_min_priority"]:
                continue
            if filters.get("outlet_max_priority") and (e.priority or 10) > filters["outlet_max_priority"]:
                continue

        # Investor-specific filters
        if target_type == "vc":
            if filters.get("investor_types"):
                if (e.investor_type or "") not in filters["investor_types"]:
                    continue
            if filters.get("investor_stages"):
                stages = e.investment_stages or []
                if not any(s in stages for s in filters["investor_stages"]):
                    continue

        # Common filters
        if filters.get("languages"):
            lang = getattr(e, "language", None) or ""
            if lang and lang not in filters["languages"]:
                continue

        if filters.get("countries"):
            country = getattr(e, "country", None) or getattr(e, "headquarters_country", None) or ""
            if country and country not in filters["countries"]:
                continue

        if filters.get("regions"):
            region = getattr(e, "region", None) or getattr(e, "headquarters_region", None) or ""
            if region and region not in filters["regions"]:
                continue

        # Email filter
        if filters.get("has_email", True):
            email = _resolve_email(e, target_type)
            if not email:
                continue

        result.append(e)
    return result


def _resolve_targets(db: Session, campaign: Campaign) -> list[dict]:
    """
    Resolve campaign target filters into a list of contact dicts.
    Returns [{id, name, email, language, target_type}, ...]
    """
    filters = campaign.target_filters or {}
    target_types = campaign.target_types or []
    override_ids = campaign.target_ids_override

    contacts = []

    if "streamer" in target_types:
        q = db.query(Streamer).filter(Streamer.is_active.is_(True))
        if override_ids:
            q = q.filter(Streamer.id.in_(override_ids))
        streamers = _apply_filters(q.all(), filters, "streamer")
        for s in streamers:
            contacts.append({
                "id": s.id,
                "name": s.name,
                "email": _resolve_email(s, "streamer"),
                "language": s.language or "en",
                "target_type": "streamer",
            })

    if "outlet" in target_types:
        q = db.query(GamingOutlet).filter(GamingOutlet.is_active.is_(True))
        if override_ids:
            q = q.filter(GamingOutlet.id.in_(override_ids))
        outlets = _apply_filters(q.all(), filters, "outlet")
        for o in outlets:
            contacts.append({
                "id": o.id,
                "name": o.name,
                "email": _resolve_email(o, "outlet"),
                "language": o.language or "en",
                "target_type": "outlet",
            })

    if "vc" in target_types:
        q = db.query(GamingInvestor).filter(GamingInvestor.is_active.is_(True))
        if override_ids:
            q = q.filter(GamingInvestor.id.in_(override_ids))
        investors = _apply_filters(q.all(), filters, "vc")
        for inv in investors:
            from app.services.message_translation_service import VC_REGION_LANGUAGE_MAP
            region = inv.headquarters_region or "GLOBAL"
            langs = VC_REGION_LANGUAGE_MAP.get(region, ["en"])
            contacts.append({
                "id": inv.id,
                "name": inv.name,
                "email": _resolve_email(inv, "vc"),
                "language": langs[0] if langs else "en",
                "target_type": "vc",
            })

    return contacts


def _get_dnc_emails(db: Session) -> set[str]:
    """Return set of all Do-Not-Contact email addresses (lowercased)."""
    rows = db.query(DoNotContact.email).all()
    return {r[0].lower() for r in rows if r[0]}


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

def preview_targets(db: Session, campaign_id: int) -> dict:
    """Preview how many targets match the campaign filters without creating records."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    contacts = _resolve_targets(db, campaign)
    dnc = _get_dnc_emails(db)

    with_email = [c for c in contacts if c["email"]]
    without_email = [c for c in contacts if not c["email"]]
    on_dnc = [c for c in with_email if c["email"].lower() in dnc]

    by_type: dict[str, int] = {}
    for c in contacts:
        by_type[c["target_type"]] = by_type.get(c["target_type"], 0) + 1

    return {
        "total": len(contacts),
        "with_email": len(with_email),
        "without_email": len(without_email),
        "on_dnc_list": len(on_dnc),
        "by_type": by_type,
    }


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------

def launch_campaign(db: Session, campaign_id: int) -> Campaign:
    """
    Launch a campaign: resolve targets, create outreach records,
    trigger personalization, schedule sends.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")
    if campaign.status != "draft":
        raise ValueError(f"Campaign must be in 'draft' status to launch (current: {campaign.status})")
    if not campaign.message_id:
        raise ValueError("Campaign must have a message_id set before launch")
    if not campaign.domain_id:
        raise ValueError("Campaign must have a domain_id set before launch")
    if not campaign.from_email:
        raise ValueError("Campaign must have a from_email set before launch")

    # Verify domain is verified
    domain = db.query(ConnectedDomain).filter(ConnectedDomain.id == campaign.domain_id).first()
    if not domain or domain.status != "verified":
        raise ValueError("Campaign domain must be verified before launch")

    contacts = _resolve_targets(db, campaign)
    dnc = _get_dnc_emails(db)

    # Create outreach records
    records = []
    for contact in contacts:
        email = contact["email"]
        skip_reason = None

        if not email:
            skip_reason = "no_email"
        elif email.lower() in dnc:
            skip_reason = "on_dnc_list"

        record = OutreachRecord(
            campaign_id=campaign.id,
            target_type=contact["target_type"],
            target_id=contact["id"],
            target_name=contact["name"],
            target_email=email,
            status="skipped" if skip_reason else "pending",
            skip_reason=skip_reason,
            follow_up_number=0,
        )
        db.add(record)
        records.append(record)

    campaign.total_targets = len(records)
    campaign.status = "personalizing"
    campaign.launched_at = datetime.now(timezone.utc)
    db.commit()

    # Trigger personalization and scheduling in background
    _process_campaign_sync(db, campaign, records)

    return campaign


def _process_campaign_sync(
    db: Session,
    campaign: Campaign,
    records: list[OutreachRecord],
) -> None:
    """
    Process campaign: personalize each target and schedule sends.
    Runs synchronously (called from background task).
    """
    message = db.query(Message).filter(Message.id == campaign.message_id).first()
    if not message:
        campaign.status = "failed"
        db.commit()
        return

    active_records = [r for r in records if r.status == "pending"]
    personalized = 0

    for record in active_records:
        try:
            record.status = "personalizing"
            db.commit()

            # Create or get personalization
            existing = (
                db.query(MessagePersonalization)
                .filter(
                    MessagePersonalization.message_id == campaign.message_id,
                    MessagePersonalization.target_type == record.target_type,
                    MessagePersonalization.target_id == record.target_id,
                )
                .first()
            )

            if existing and existing.status == "completed":
                p = existing
            else:
                if existing:
                    p = existing
                    p.status = "pending"
                else:
                    p = MessagePersonalization(
                        message_id=campaign.message_id,
                        target_type=record.target_type,
                        target_id=record.target_id,
                        target_name=record.target_name,
                        target_language=_get_contact_language(db, record),
                        status="pending",
                    )
                    db.add(p)
                    db.commit()
                    db.refresh(p)

                personalize_and_translate(db, p, message)
                db.refresh(p)

            record.personalization_id = p.id
            if p.status == "completed":
                record.status = "personalized"
                personalized += 1
            else:
                record.status = "failed"
                record.error_message = p.error_message or "Personalization failed"

            db.commit()

        except Exception as exc:
            logger.error("Personalization failed for record %s: %s", record.id, exc)
            record.status = "failed"
            record.error_message = str(exc)
            db.commit()

    campaign.personalized_count = personalized

    # Schedule sends
    sendable = [r for r in records if r.status == "personalized"]
    _schedule_sends(campaign, sendable)

    campaign.status = "scheduled" if sendable else "completed"
    if not sendable:
        campaign.completed_at = datetime.now(timezone.utc)
    db.commit()


def _get_contact_language(db: Session, record: OutreachRecord) -> str:
    """Determine the language for a contact."""
    if record.target_type == "streamer":
        s = db.query(Streamer).filter(Streamer.id == record.target_id).first()
        return (s.language if s else None) or "en"
    elif record.target_type == "outlet":
        o = db.query(GamingOutlet).filter(GamingOutlet.id == record.target_id).first()
        return (o.language if o else None) or "en"
    elif record.target_type == "vc":
        from app.services.message_translation_service import VC_REGION_LANGUAGE_MAP
        inv = db.query(GamingInvestor).filter(GamingInvestor.id == record.target_id).first()
        if inv:
            region = inv.headquarters_region or "GLOBAL"
            langs = VC_REGION_LANGUAGE_MAP.get(region, ["en"])
            return langs[0] if langs else "en"
    return "en"


def _schedule_sends(campaign: Campaign, records: list[OutreachRecord]) -> None:
    """Assign scheduled_send_at timestamps based on campaign batch config."""
    start = campaign.send_start_at or datetime.now(timezone.utc)
    batch_size = campaign.batch_size or 20
    delay = timedelta(seconds=campaign.batch_delay_seconds or 300)

    for i, record in enumerate(records):
        batch_num = i // batch_size
        record.scheduled_send_at = start + (delay * batch_num)
        record.status = "personalized"  # ready for send processor


# ---------------------------------------------------------------------------
# Send processor (called by APScheduler)
# ---------------------------------------------------------------------------

def campaign_send_processor_job():
    """
    APScheduler job: sends the next batch of outreach emails for active campaigns.
    Creates its own DB session (runs in background thread).
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        _process_sends(db)
    except Exception as exc:
        logger.error("Campaign send processor error: %s", exc)
    finally:
        db.close()


def _process_sends(db: Session) -> None:
    """Send outreach records that are due."""
    now = datetime.now(timezone.utc)

    # Find campaigns that are scheduled or sending
    campaigns = (
        db.query(Campaign)
        .filter(Campaign.status.in_(["scheduled", "sending"]))
        .all()
    )

    for campaign in campaigns:
        # Check send window
        if not _in_send_window(campaign, now):
            continue

        # Get next batch of records ready to send
        records = (
            db.query(OutreachRecord)
            .filter(
                OutreachRecord.campaign_id == campaign.id,
                OutreachRecord.status == "personalized",
                OutreachRecord.scheduled_send_at <= now,
            )
            .order_by(OutreachRecord.scheduled_send_at)
            .limit(campaign.batch_size or 20)
            .all()
        )

        if not records:
            # Check if all records are done
            remaining = (
                db.query(OutreachRecord)
                .filter(
                    OutreachRecord.campaign_id == campaign.id,
                    OutreachRecord.status.in_(["pending", "personalizing", "personalized"]),
                )
                .count()
            )
            if remaining == 0:
                campaign.status = "completed"
                campaign.completed_at = datetime.now(timezone.utc)
                db.commit()
            continue

        if campaign.status == "scheduled":
            campaign.status = "sending"
            db.commit()

        for record in records:
            _send_single_outreach(db, campaign, record)


def _in_send_window(campaign: Campaign, now: datetime) -> bool:
    """Check if current time is within the campaign's send window."""
    if not campaign.send_window_start or not campaign.send_window_end:
        return True

    try:
        hour_min = now.strftime("%H:%M")
        return campaign.send_window_start <= hour_min <= campaign.send_window_end
    except Exception:
        return True


def _send_single_outreach(
    db: Session, campaign: Campaign, record: OutreachRecord,
) -> None:
    """Send a single outreach email."""
    try:
        if not record.target_email:
            record.status = "skipped"
            record.skip_reason = "no_email"
            db.commit()
            return

        # Get personalized content
        p = (
            db.query(MessagePersonalization)
            .filter(MessagePersonalization.id == record.personalization_id)
            .first()
        )
        if not p or p.status != "completed":
            record.status = "failed"
            record.error_message = "Personalization not ready"
            campaign.failed_count = (campaign.failed_count or 0) + 1
            db.commit()
            return

        subject = p.personalized_title
        body_html = f"<div>{p.personalized_body}</div>"
        body_text = p.personalized_body

        # Send via email service
        sent_email = email_service.send_email(
            db=db,
            domain_id=campaign.domain_id,
            from_email=campaign.from_email,
            to=[record.target_email],
            subject=subject,
            html=body_html,
            text=body_text,
            from_name=campaign.from_name,
            reply_to=campaign.reply_to,
            tags=[f"campaign:{campaign.id}", f"target:{record.target_type}"],
        )

        record.sent_email_id = sent_email.id
        record.sent_at = datetime.now(timezone.utc)

        if sent_email.status == "sent":
            record.status = "sent"
            campaign.sent_count = (campaign.sent_count or 0) + 1
        else:
            record.status = "failed"
            record.error_message = sent_email.error_message
            campaign.failed_count = (campaign.failed_count or 0) + 1

        db.commit()

    except Exception as exc:
        logger.error("Failed to send outreach %s: %s", record.id, exc)
        record.status = "failed"
        record.error_message = str(exc)
        campaign.failed_count = (campaign.failed_count or 0) + 1
        db.commit()


# ---------------------------------------------------------------------------
# Pause / Resume
# ---------------------------------------------------------------------------

def pause_campaign(db: Session, campaign_id: int) -> Campaign:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")
    if campaign.status not in ("scheduled", "sending"):
        raise ValueError(f"Cannot pause campaign in '{campaign.status}' status")
    campaign.status = "paused"
    db.commit()
    db.refresh(campaign)
    return campaign


def resume_campaign(db: Session, campaign_id: int) -> Campaign:
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")
    if campaign.status != "paused":
        raise ValueError("Campaign is not paused")

    # Reschedule unsent records
    unsent = (
        db.query(OutreachRecord)
        .filter(
            OutreachRecord.campaign_id == campaign_id,
            OutreachRecord.status == "personalized",
        )
        .all()
    )
    _schedule_sends(campaign, unsent)
    campaign.status = "scheduled"
    db.commit()
    db.refresh(campaign)
    return campaign


# ---------------------------------------------------------------------------
# Follow-up processor (called by APScheduler)
# ---------------------------------------------------------------------------

def campaign_follow_up_processor_job():
    """APScheduler job: create follow-up outreach for non-responders."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        _process_follow_ups(db)
    except Exception as exc:
        logger.error("Campaign follow-up processor error: %s", exc)
    finally:
        db.close()


def _process_follow_ups(db: Session) -> None:
    """Find campaigns with follow-ups enabled and create follow-up records."""
    campaigns = (
        db.query(Campaign)
        .filter(
            Campaign.follow_up_enabled.is_(True),
            Campaign.status.in_(["sending", "completed"]),
        )
        .all()
    )

    now = datetime.now(timezone.utc)

    for campaign in campaigns:
        delay = timedelta(days=campaign.follow_up_delay_days or 3)
        max_fu = campaign.max_follow_ups or 1
        fu_message_id = campaign.follow_up_message_id or campaign.message_id

        # Find initial outreach records that were sent but not opened/clicked/replied
        candidates = (
            db.query(OutreachRecord)
            .filter(
                OutreachRecord.campaign_id == campaign.id,
                OutreachRecord.follow_up_number < max_fu,
                OutreachRecord.status.in_(["sent", "delivered"]),
                OutreachRecord.sent_at.isnot(None),
                OutreachRecord.sent_at <= now - delay,
                OutreachRecord.opened_at.is_(None),
                OutreachRecord.replied_at.is_(None),
            )
            .all()
        )

        for original in candidates:
            # Check if follow-up already exists
            existing = (
                db.query(OutreachRecord)
                .filter(
                    OutreachRecord.campaign_id == campaign.id,
                    OutreachRecord.target_type == original.target_type,
                    OutreachRecord.target_id == original.target_id,
                    OutreachRecord.follow_up_number == original.follow_up_number + 1,
                )
                .first()
            )
            if existing:
                continue

            fu_record = OutreachRecord(
                campaign_id=campaign.id,
                target_type=original.target_type,
                target_id=original.target_id,
                target_name=original.target_name,
                target_email=original.target_email,
                status="pending",
                follow_up_number=original.follow_up_number + 1,
                parent_outreach_id=original.id,
            )
            db.add(fu_record)
            db.commit()
            db.refresh(fu_record)

            # Personalize the follow-up
            fu_message = db.query(Message).filter(Message.id == fu_message_id).first()
            if not fu_message:
                continue

            p = MessagePersonalization(
                message_id=fu_message_id,
                target_type=fu_record.target_type,
                target_id=fu_record.target_id,
                target_name=fu_record.target_name,
                target_language=_get_contact_language(db, fu_record),
                status="pending",
            )
            db.add(p)
            db.commit()
            db.refresh(p)

            try:
                personalize_and_translate(db, p, fu_message, is_follow_up=True)
                db.refresh(p)

                fu_record.personalization_id = p.id
                if p.status == "completed":
                    fu_record.status = "personalized"
                    fu_record.scheduled_send_at = datetime.now(timezone.utc)
                else:
                    fu_record.status = "failed"
                    fu_record.error_message = p.error_message
            except Exception as exc:
                fu_record.status = "failed"
                fu_record.error_message = str(exc)

            db.commit()

        # Re-activate campaign if follow-ups were created
        if campaign.status == "completed":
            has_pending = (
                db.query(OutreachRecord)
                .filter(
                    OutreachRecord.campaign_id == campaign.id,
                    OutreachRecord.status == "personalized",
                )
                .count()
            )
            if has_pending > 0:
                campaign.status = "sending"
                campaign.completed_at = None
                db.commit()


# ---------------------------------------------------------------------------
# Event sync (called by APScheduler)
# ---------------------------------------------------------------------------

def campaign_event_sync_job():
    """APScheduler job: sync email tracking events back to outreach records."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        _sync_events(db)
    except Exception as exc:
        logger.error("Campaign event sync error: %s", exc)
    finally:
        db.close()


def _sync_events(db: Session) -> None:
    """Sync SentEmail opens/clicks/bounces to OutreachRecords and Campaign counters."""
    # Get all outreach records that have a sent_email_id and are in sent/delivered status
    records = (
        db.query(OutreachRecord)
        .filter(
            OutreachRecord.sent_email_id.isnot(None),
            OutreachRecord.status.in_(["sent", "delivered"]),
        )
        .all()
    )

    for record in records:
        email = db.query(SentEmail).filter(SentEmail.id == record.sent_email_id).first()
        if not email:
            continue

        campaign = db.query(Campaign).filter(Campaign.id == record.campaign_id).first()

        # Sync delivery status
        if email.status == "delivered" and record.status == "sent":
            record.status = "delivered"
            if campaign:
                campaign.delivered_count = (campaign.delivered_count or 0) + 1

        elif email.status == "bounced":
            record.status = "bounced"
            if campaign:
                campaign.bounced_count = (campaign.bounced_count or 0) + 1

            # Add to DNC
            if record.target_email:
                existing_dnc = (
                    db.query(DoNotContact)
                    .filter(DoNotContact.email == record.target_email.lower())
                    .first()
                )
                if not existing_dnc:
                    dnc = DoNotContact(
                        email=record.target_email.lower(),
                        reason="bounced",
                        source=f"campaign:{record.campaign_id}",
                    )
                    db.add(dnc)

        # Sync opens
        if email.opens and email.opens > 0 and not record.opened_at:
            record.opened_at = datetime.now(timezone.utc)
            record.status = "opened"
            if campaign:
                campaign.opened_count = (campaign.opened_count or 0) + 1

        # Sync clicks
        if email.clicks and email.clicks > 0 and not record.clicked_at:
            record.clicked_at = datetime.now(timezone.utc)
            record.status = "clicked"
            if campaign:
                campaign.clicked_count = (campaign.clicked_count or 0) + 1

    db.commit()


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_campaign_stats(db: Session, campaign_id: int) -> dict:
    """Get detailed campaign analytics."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError(f"Campaign {campaign_id} not found")

    # Count by status
    status_counts = (
        db.query(OutreachRecord.status, func.count(OutreachRecord.id))
        .filter(OutreachRecord.campaign_id == campaign_id)
        .group_by(OutreachRecord.status)
        .all()
    )
    counts = dict(status_counts)

    skipped = counts.get("skipped", 0)
    sent = campaign.sent_count or 0
    delivered = campaign.delivered_count or 0
    opened = campaign.opened_count or 0
    clicked = campaign.clicked_count or 0
    replied = campaign.replied_count or 0
    bounced = campaign.bounced_count or 0
    failed = campaign.failed_count or 0

    # By target type
    type_counts = (
        db.query(
            OutreachRecord.target_type,
            OutreachRecord.status,
            func.count(OutreachRecord.id),
        )
        .filter(OutreachRecord.campaign_id == campaign_id)
        .group_by(OutreachRecord.target_type, OutreachRecord.status)
        .all()
    )
    by_type: dict = {}
    for ttype, status, count in type_counts:
        if ttype not in by_type:
            by_type[ttype] = {}
        by_type[ttype][status] = count

    denom = max(delivered, 1)
    return {
        "total_targets": campaign.total_targets or 0,
        "skipped": skipped,
        "personalized": campaign.personalized_count or 0,
        "sent": sent,
        "delivered": delivered,
        "opened": opened,
        "clicked": clicked,
        "replied": replied,
        "bounced": bounced,
        "failed": failed,
        "open_rate": round(opened / denom, 3),
        "click_rate": round(clicked / denom, 3),
        "reply_rate": round(replied / denom, 3),
        "bounce_rate": round(bounced / max(sent, 1), 3),
        "by_target_type": by_type,
    }


# ---------------------------------------------------------------------------
# Outreach record listing
# ---------------------------------------------------------------------------

def list_outreach_records(
    db: Session,
    campaign_id: int,
    status: Optional[str] = None,
    target_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[OutreachRecord], int]:
    q = db.query(OutreachRecord).filter(OutreachRecord.campaign_id == campaign_id)
    if status:
        q = q.filter(OutreachRecord.status == status)
    if target_type:
        q = q.filter(OutreachRecord.target_type == target_type)

    total = q.count()
    records = q.order_by(OutreachRecord.created_at.desc()).offset(skip).limit(limit).all()
    return records, total


# ---------------------------------------------------------------------------
# DNC management
# ---------------------------------------------------------------------------

def add_to_dnc(db: Session, email: str, reason: str = "manual", source: Optional[str] = None) -> DoNotContact:
    existing = db.query(DoNotContact).filter(DoNotContact.email == email.lower()).first()
    if existing:
        return existing
    dnc = DoNotContact(email=email.lower(), reason=reason, source=source)
    db.add(dnc)
    db.commit()
    db.refresh(dnc)
    return dnc


def remove_from_dnc(db: Session, dnc_id: int) -> bool:
    dnc = db.query(DoNotContact).filter(DoNotContact.id == dnc_id).first()
    if not dnc:
        return False
    db.delete(dnc)
    db.commit()
    return True


def list_dnc(db: Session, skip: int = 0, limit: int = 100) -> list[DoNotContact]:
    return (
        db.query(DoNotContact)
        .order_by(DoNotContact.created_at.desc())
        .offset(skip).limit(limit).all()
    )
