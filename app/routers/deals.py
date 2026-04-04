"""Deal and sponsorship tracking endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas.deal import (
    DealCreate, DealPipelineSummary, DealResponse,
    DealStageChange, DealStageHistoryResponse, DealUpdate,
)
from app.services import deal_service

router = APIRouter(prefix="/api/deals", tags=["Deals"])


@router.post("/", response_model=DealResponse, status_code=201)
def create_deal(
    payload: DealCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new deal."""
    return deal_service.create_deal(db, payload.model_dump(), user.id)


@router.get("/", response_model=list[DealResponse])
def list_deals(
    company_id: Optional[int] = None,
    deal_type: Optional[str] = None,
    stage: Optional[str] = None,
    contact_type: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List deals with filters."""
    return deal_service.list_deals(db, company_id, deal_type, stage, contact_type, limit, offset)


@router.get("/pipeline")
def pipeline(
    company_id: Optional[int] = None,
    deal_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Pipeline view: deals grouped by stage."""
    return deal_service.get_pipeline(db, company_id, deal_type)


@router.get("/summary", response_model=DealPipelineSummary)
def deal_summary(
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Aggregate deal statistics."""
    return deal_service.get_deal_summary(db, company_id)


@router.get("/{deal_id}", response_model=DealResponse)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    """Get a single deal."""
    try:
        return deal_service.get_deal(db, deal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{deal_id}", response_model=DealResponse)
def update_deal(
    deal_id: int,
    payload: DealUpdate,
    db: Session = Depends(get_db),
):
    """Update deal fields."""
    try:
        return deal_service.update_deal(db, deal_id, payload.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{deal_id}/stage", response_model=DealResponse)
def change_stage(
    deal_id: int,
    payload: DealStageChange,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Change a deal's stage."""
    try:
        return deal_service.change_stage(db, deal_id, payload.new_stage, payload.notes, user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{deal_id}/history", response_model=list[DealStageHistoryResponse])
def stage_history(deal_id: int, db: Session = Depends(get_db)):
    """Get stage transition history for a deal."""
    return deal_service.get_stage_history(db, deal_id)


@router.delete("/{deal_id}")
def delete_deal(deal_id: int, db: Session = Depends(get_db)):
    """Delete a deal."""
    if not deal_service.delete_deal(db, deal_id):
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"deleted": True}
