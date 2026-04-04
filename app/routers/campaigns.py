"""Campaign management and outreach automation endpoints."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.campaign import (
    CampaignCreate,
    CampaignPreviewResponse,
    CampaignResponse,
    CampaignStatsResponse,
    CampaignUpdate,
    DNCCreate,
    DNCResponse,
    OutreachRecordResponse,
)
from app.services import campaign_service

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


# ---------------------------------------------------------------------------
# Campaign CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=CampaignResponse, status_code=201)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Create a new outreach campaign in draft status."""
    data = payload.model_dump()
    campaign = campaign_service.create_campaign(db, data)
    return campaign


@router.get("/", response_model=list[CampaignResponse])
def list_campaigns(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List campaigns with optional status filter."""
    return campaign_service.list_campaigns(db, status=status, skip=skip, limit=limit)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get a single campaign."""
    campaign = campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Update a campaign (draft status only)."""
    try:
        data = payload.model_dump(exclude_none=True)
        return campaign_service.update_campaign(db, campaign_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Delete a campaign (draft status only)."""
    try:
        if not campaign_service.delete_campaign(db, campaign_id):
            raise HTTPException(status_code=404, detail="Campaign not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Preview & Launch
# ---------------------------------------------------------------------------

@router.post("/{campaign_id}/preview", response_model=CampaignPreviewResponse)
def preview_targets(
    campaign_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Preview how many targets match the campaign filters without sending."""
    try:
        return campaign_service.preview_targets(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _run_launch(campaign_id: int):
    """Background task: launch campaign pipeline."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        campaign_service.launch_campaign(db, campaign_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Campaign launch failed: %s", e)
    finally:
        db.close()


@router.post("/{campaign_id}/launch", response_model=CampaignResponse)
def launch_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Launch a campaign. Resolves targets, personalizes messages with Claude AI,
    and schedules staggered email delivery.

    The pipeline runs in the background — poll GET /campaigns/{id} for status updates.
    """
    campaign = campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Campaign must be in 'draft' status to launch (current: {campaign.status})",
        )

    # Validate required fields before launching
    for field in ("message_id", "domain_id", "from_email"):
        if not getattr(campaign, field):
            raise HTTPException(
                status_code=400,
                detail=f"Campaign must have '{field}' set before launch",
            )

    background_tasks.add_task(_run_launch, campaign_id)

    # Return current state (will be "draft" since background hasn't started yet)
    return campaign


# ---------------------------------------------------------------------------
# Pause / Resume
# ---------------------------------------------------------------------------

@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
def pause_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Pause a sending campaign."""
    try:
        return campaign_service.pause_campaign(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/resume", response_model=CampaignResponse)
def resume_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Resume a paused campaign."""
    try:
        return campaign_service.resume_campaign(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Outreach records & stats
# ---------------------------------------------------------------------------

@router.get("/{campaign_id}/outreach", response_model=list[OutreachRecordResponse])
def list_outreach(
    campaign_id: int,
    status: Optional[str] = None,
    target_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List outreach records for a campaign with optional filters."""
    records, _ = campaign_service.list_outreach_records(
        db, campaign_id, status=status, target_type=target_type, skip=skip, limit=limit,
    )
    return records


@router.get("/{campaign_id}/stats", response_model=CampaignStatsResponse)
def campaign_stats(campaign_id: int, db: Session = Depends(get_db)):
    """Get detailed campaign analytics: sent, opened, clicked, replied, bounce rates."""
    try:
        return campaign_service.get_campaign_stats(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/sync-events", response_model=CampaignResponse)
def sync_events(
    campaign_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Manually trigger email event sync (opens, clicks, bounces) for a campaign."""
    campaign = campaign_service.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign_service._sync_events(db)
    db.refresh(campaign)
    return campaign


# ---------------------------------------------------------------------------
# Do Not Contact
# ---------------------------------------------------------------------------

@router.get("/dnc/list", response_model=list[DNCResponse])
def list_dnc(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all Do-Not-Contact entries."""
    return campaign_service.list_dnc(db, skip=skip, limit=limit)


@router.post("/dnc", response_model=DNCResponse, status_code=201)
def add_dnc(
    payload: DNCCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Add an email to the Do-Not-Contact blocklist."""
    return campaign_service.add_to_dnc(db, email=payload.email, reason=payload.reason)


@router.delete("/dnc/{dnc_id}", status_code=204)
def remove_dnc(
    dnc_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Remove an email from the Do-Not-Contact blocklist."""
    if not campaign_service.remove_from_dnc(db, dnc_id):
        raise HTTPException(status_code=404, detail="DNC entry not found")
