"""CRM endpoints — contact timeline, notes, relationship stages, pipeline."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.crm import ActivityResponse, NoteCreate, PipelineSummary, StageUpdate
from app.services import crm_service

router = APIRouter(prefix="/api/crm", tags=["CRM"])


@router.get("/pipeline", response_model=PipelineSummary)
def pipeline(db: Session = Depends(get_db)):
    """Pipeline overview: contacts grouped by relationship stage."""
    return crm_service.get_pipeline_summary(db)


@router.get("/recent", response_model=list[ActivityResponse])
def recent_activity(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Recent activity feed across all contacts."""
    return crm_service.get_recent_activity(db, limit)


@router.get("/timeline/{contact_type}/{contact_id}", response_model=list[ActivityResponse])
def timeline(
    contact_type: str,
    contact_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Full interaction timeline for a specific contact."""
    return crm_service.get_timeline(db, contact_type, contact_id, limit, offset)


@router.post("/note/{contact_type}/{contact_id}", response_model=ActivityResponse)
def add_note(
    contact_type: str,
    contact_id: int,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Add a manual note to a contact's timeline."""
    return crm_service.add_note(db, contact_type, contact_id, payload.note, user.id)


@router.put("/stage/{contact_type}/{contact_id}")
def update_stage(
    contact_type: str,
    contact_id: int,
    payload: StageUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update a contact's relationship stage."""
    try:
        new_stage = crm_service.update_relationship_stage(
            db, contact_type, contact_id, payload.stage, user.id,
        )
        return {"contact_type": contact_type, "contact_id": contact_id, "stage": new_stage}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
