from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.outreach import OutreachMessage
from app.schemas.outreach import GenerateMessageRequest, OutreachMessageResponse, OutreachStatsResponse
from app.services.message_generator import generate_message
from app.services.contact_scraper import (
    scrape_outlet_website, scrape_streamer_website, scrape_vc_website,
    scrape_all_outlets, scrape_all_streamers, scrape_all_vcs,
)

router = APIRouter(prefix="/api/outreach", tags=["outreach"])


# ─── Message Generation ───

@router.post("/generate", response_model=OutreachMessageResponse, status_code=201)
def generate_outreach_message(req: GenerateMessageRequest, db: Session = Depends(get_db)):
    """Generate a personalized outreach message for an outlet, streamer, or gaming VC."""
    try:
        msg = generate_message(
            db=db,
            target_type=req.target_type,
            target_id=req.target_id,
            message_type=req.message_type,
            tone=req.tone,
            game_title=req.game_title,
            game_description=req.game_description,
            key_selling_points=req.key_selling_points,
            custom_context=req.custom_context,
        )
        return msg
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/messages", response_model=list[OutreachMessageResponse])
def list_messages(
    target_type: Optional[str] = None,
    message_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
):
    """List outreach messages with optional filters."""
    query = db.query(OutreachMessage)
    if target_type:
        query = query.filter(OutreachMessage.target_type == target_type)
    if message_type:
        query = query.filter(OutreachMessage.message_type == message_type)
    if status:
        query = query.filter(OutreachMessage.status == status)
    return (
        query.order_by(OutreachMessage.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )


@router.get("/messages/{message_id}", response_model=OutreachMessageResponse)
def get_message(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(OutreachMessage).filter(OutreachMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


@router.delete("/messages/{message_id}", status_code=204)
def delete_message(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(OutreachMessage).filter(OutreachMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()


@router.get("/stats", response_model=OutreachStatsResponse)
def outreach_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(OutreachMessage.id)).scalar()
    by_type = dict(
        db.query(OutreachMessage.message_type, func.count(OutreachMessage.id))
        .group_by(OutreachMessage.message_type).all()
    )
    by_target = dict(
        db.query(OutreachMessage.target_type, func.count(OutreachMessage.id))
        .group_by(OutreachMessage.target_type).all()
    )
    by_status = dict(
        db.query(OutreachMessage.status, func.count(OutreachMessage.id))
        .group_by(OutreachMessage.status).all()
    )
    total_sent = db.query(func.count(OutreachMessage.id)).filter(OutreachMessage.status == "sent").scalar()
    total_opened = db.query(func.count(OutreachMessage.id)).filter(OutreachMessage.was_opened.is_(True)).scalar()
    total_replied = db.query(func.count(OutreachMessage.id)).filter(OutreachMessage.was_replied.is_(True)).scalar()

    return OutreachStatsResponse(
        total_messages=total,
        messages_by_type=by_type,
        messages_by_target=by_target,
        messages_by_status=by_status,
        total_sent=total_sent,
        total_opened=total_opened,
        total_replied=total_replied,
        open_rate=total_opened / total_sent if total_sent > 0 else 0.0,
        reply_rate=total_replied / total_sent if total_sent > 0 else 0.0,
    )


# ─── Scraping Endpoints ───

@router.post("/scrape/outlet/{outlet_id}")
def scrape_outlet(outlet_id: int, db: Session = Depends(get_db)):
    """Scrape an outlet's website for additional data."""
    return scrape_outlet_website(db, outlet_id)


@router.post("/scrape/streamer/{streamer_id}")
def scrape_streamer(streamer_id: int, db: Session = Depends(get_db)):
    """Scrape a streamer's pages for additional data."""
    return scrape_streamer_website(db, streamer_id)


@router.post("/scrape/gaming-vc/{vc_id}")
def scrape_gaming_vc(vc_id: int, db: Session = Depends(get_db)):
    """Scrape a gaming VC's website for additional data."""
    return scrape_vc_website(db, vc_id)


@router.post("/scrape/all-outlets")
def scrape_all_outlets_endpoint(db: Session = Depends(get_db)):
    """Scrape all active outlets' websites for enrichment data."""
    return scrape_all_outlets(db)


@router.post("/scrape/all-streamers")
def scrape_all_streamers_endpoint(db: Session = Depends(get_db)):
    """Scrape all active streamers' pages for enrichment data."""
    return scrape_all_streamers(db)


@router.post("/scrape/all-gaming-vcs")
def scrape_all_vcs_endpoint(db: Session = Depends(get_db)):
    """Scrape all active VCs' websites for enrichment data."""
    return scrape_all_vcs(db)
