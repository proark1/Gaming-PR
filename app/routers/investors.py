from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.investor import GamingInvestor
from app.schemas.investor import InvestorCreate, InvestorUpdate, InvestorResponse
from app.services.profile_service import save_investor_profile

router = APIRouter(prefix="/api/investors", tags=["investors"])


@router.get("/", response_model=list[InvestorResponse])
def list_investors(
    investor_type: Optional[str] = Query(None, description="Filter by type: vc, pe, angel, corporate, accelerator"),
    focus_area: Optional[str] = Query(None, description="Filter by focus area (partial match in JSON array)"),
    region: Optional[str] = Query(None, description="Filter by headquarters region: US, EU, ASIA, etc."),
    is_active: Optional[bool] = Query(None),
    is_gaming_focused: Optional[bool] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(GamingInvestor)
    if investor_type:
        q = q.filter(GamingInvestor.investor_type == investor_type)
    if region:
        q = q.filter(GamingInvestor.headquarters_region == region.upper())
    if is_active is not None:
        q = q.filter(GamingInvestor.is_active == is_active)
    if is_gaming_focused is not None:
        q = q.filter(GamingInvestor.is_gaming_focused == is_gaming_focused)
    if focus_area:
        # JSON array contains check — works for PostgreSQL JSONB cast
        q = q.filter(
            func.cast(GamingInvestor.focus_areas, func.text()).contains(focus_area)
        )
    return q.order_by(GamingInvestor.name).offset(offset).limit(limit).all()


@router.get("/stats")
def investor_stats(db: Session = Depends(get_db)):
    from sqlalchemy import case
    row = db.query(
        func.count(GamingInvestor.id).label("total"),
        func.sum(case((GamingInvestor.is_active == True, 1), else_=0)).label("active"),
        func.sum(case((GamingInvestor.is_gaming_focused == True, 1), else_=0)).label("gaming_focused"),
    ).one()

    by_type = dict(
        db.query(GamingInvestor.investor_type, func.count(GamingInvestor.id))
        .group_by(GamingInvestor.investor_type)
        .all()
    )
    by_region = dict(
        db.query(GamingInvestor.headquarters_region, func.count(GamingInvestor.id))
        .filter(GamingInvestor.headquarters_region.isnot(None))
        .group_by(GamingInvestor.headquarters_region)
        .all()
    )
    return {
        "total": row.total or 0,
        "active": row.active or 0,
        "gaming_focused": row.gaming_focused or 0,
        "by_type": by_type,
        "by_region": by_region,
    }


@router.get("/{investor_id}", response_model=InvestorResponse)
def get_investor(investor_id: int, db: Session = Depends(get_db)):
    investor = db.query(GamingInvestor).filter(GamingInvestor.id == investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    return investor


@router.post("/", response_model=InvestorResponse, status_code=201)
def create_investor(payload: InvestorCreate, db: Session = Depends(get_db)):
    existing = db.query(GamingInvestor).filter(GamingInvestor.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Investor '{payload.name}' already exists")
    investor = GamingInvestor(**payload.model_dump())
    db.add(investor)
    db.commit()
    db.refresh(investor)
    save_investor_profile(db, investor)
    return investor


@router.put("/{investor_id}", response_model=InvestorResponse)
def update_investor(investor_id: int, payload: InvestorUpdate, db: Session = Depends(get_db)):
    investor = db.query(GamingInvestor).filter(GamingInvestor.id == investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(investor, field, value)
    db.commit()
    db.refresh(investor)
    save_investor_profile(db, investor)
    return investor


@router.post("/{investor_id}/refresh-profile", response_model=InvestorResponse)
def refresh_investor_profile(investor_id: int, db: Session = Depends(get_db)):
    """Recompile and save the outreach profile from current investor data."""
    investor = db.query(GamingInvestor).filter(GamingInvestor.id == investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    save_investor_profile(db, investor)
    return investor


@router.delete("/{investor_id}", status_code=204)
def delete_investor(investor_id: int, db: Session = Depends(get_db)):
    investor = db.query(GamingInvestor).filter(GamingInvestor.id == investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    db.delete(investor)
    db.commit()
