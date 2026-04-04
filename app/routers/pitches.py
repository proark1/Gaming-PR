"""AI Pitch Generator endpoints — generate, approve, and send tailored pitches."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.pitch import (
    PitchApproveRequest, PitchBulkGenerateRequest,
    PitchGenerateRequest, PitchResponse, PitchSendRequest,
)
from app.services import pitch_service

router = APIRouter(prefix="/api/pitches", tags=["Pitches"])


@router.post("/generate", response_model=PitchResponse)
def generate_pitch(
    payload: PitchGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate a single AI pitch for a specific contact."""
    try:
        return pitch_service.generate_pitch(
            db, payload.company_id, payload.target_type, payload.target_id,
            payload.pitch_type, payload.user_instructions or "", payload.tone,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/generate-bulk", response_model=list[PitchResponse])
def generate_bulk(
    payload: PitchBulkGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate pitches for multiple targets (runs in background for large batches)."""
    try:
        return pitch_service.generate_bulk_pitches(
            db, payload.company_id, payload.target_type, payload.target_ids,
            payload.pitch_type, payload.user_instructions or "", payload.tone,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=list[PitchResponse])
def list_pitches(
    company_id: Optional[int] = None,
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List generated pitches with optional filters."""
    return pitch_service.list_pitches(db, company_id, target_type, status, limit, offset)


@router.get("/{pitch_id}", response_model=PitchResponse)
def get_pitch(pitch_id: int, db: Session = Depends(get_db)):
    """Get a single pitch by ID."""
    from app.models.pitch import GeneratedPitch
    pitch = db.query(GeneratedPitch).filter(GeneratedPitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    return pitch


@router.post("/{pitch_id}/approve", response_model=PitchResponse)
def approve_pitch(
    pitch_id: int,
    payload: PitchApproveRequest,
    db: Session = Depends(get_db),
):
    """Approve a pitch, optionally editing subject/body."""
    try:
        return pitch_service.approve_pitch(
            db, pitch_id, payload.edited_subject, payload.edited_body,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{pitch_id}")
def delete_pitch(pitch_id: int, db: Session = Depends(get_db)):
    """Delete a pitch."""
    from app.models.pitch import GeneratedPitch
    pitch = db.query(GeneratedPitch).filter(GeneratedPitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    db.delete(pitch)
    db.commit()
    return {"deleted": True}
