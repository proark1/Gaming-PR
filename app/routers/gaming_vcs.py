from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.gaming_vc import GamingVC
from app.schemas.gaming_vc import GamingVCCreate, GamingVCUpdate, GamingVCResponse, GamingVCStatsResponse
from app.services.contact_scraper import scrape_vc_website

router = APIRouter(prefix="/api/gaming-vcs", tags=["gaming_vcs"])


@router.get("/", response_model=list[GamingVCResponse])
def list_gaming_vcs(
    firm_type: Optional[str] = None,
    tier: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(GamingVC)
    if firm_type:
        query = query.filter(GamingVC.firm_type == firm_type)
    if tier:
        query = query.filter(GamingVC.tier == tier)
    if is_active is not None:
        query = query.filter(GamingVC.is_active == is_active)
    if search:
        query = query.filter(GamingVC.name.ilike(f"%{search}%"))
    return query.order_by(GamingVC.priority.asc(), GamingVC.name).all()


@router.get("/stats", response_model=GamingVCStatsResponse)
def gaming_vc_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(GamingVC.id)).scalar()
    active = db.query(func.count(GamingVC.id)).filter(GamingVC.is_active.is_(True)).scalar()
    by_type = dict(
        db.query(GamingVC.firm_type, func.count(GamingVC.id))
        .filter(GamingVC.firm_type.isnot(None))
        .group_by(GamingVC.firm_type)
        .all()
    )
    by_tier = dict(
        db.query(GamingVC.tier, func.count(GamingVC.id))
        .filter(GamingVC.tier.isnot(None))
        .group_by(GamingVC.tier)
        .all()
    )
    # Count by investment stage (flatten JSON arrays)
    all_vcs = db.query(GamingVC).all()
    stage_counts = {}
    total_portfolio = 0
    for vc in all_vcs:
        if vc.investment_stage:
            for stage in vc.investment_stage:
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
        if vc.portfolio_companies_count:
            total_portfolio += vc.portfolio_companies_count

    return GamingVCStatsResponse(
        total_vcs=total,
        active_vcs=active,
        vcs_by_type=by_type,
        vcs_by_tier=by_tier,
        vcs_by_stage=stage_counts,
        total_portfolio_companies=total_portfolio,
    )


@router.get("/{vc_id}", response_model=GamingVCResponse)
def get_gaming_vc(vc_id: int, db: Session = Depends(get_db)):
    vc = db.query(GamingVC).filter(GamingVC.id == vc_id).first()
    if not vc:
        raise HTTPException(status_code=404, detail="Gaming VC not found")
    return vc


@router.post("/", response_model=GamingVCResponse, status_code=201)
def create_gaming_vc(data: GamingVCCreate, db: Session = Depends(get_db)):
    existing = db.query(GamingVC).filter(GamingVC.url == data.url).first()
    if existing:
        raise HTTPException(status_code=409, detail="Gaming VC with this URL already exists")
    vc = GamingVC(**data.model_dump())
    db.add(vc)
    db.commit()
    db.refresh(vc)
    return vc


@router.patch("/{vc_id}", response_model=GamingVCResponse)
def update_gaming_vc(vc_id: int, data: GamingVCUpdate, db: Session = Depends(get_db)):
    vc = db.query(GamingVC).filter(GamingVC.id == vc_id).first()
    if not vc:
        raise HTTPException(status_code=404, detail="Gaming VC not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vc, field, value)
    db.commit()
    db.refresh(vc)
    return vc


@router.delete("/{vc_id}", status_code=204)
def delete_gaming_vc(vc_id: int, db: Session = Depends(get_db)):
    vc = db.query(GamingVC).filter(GamingVC.id == vc_id).first()
    if not vc:
        raise HTTPException(status_code=404, detail="Gaming VC not found")
    db.delete(vc)
    db.commit()


@router.post("/{vc_id}/scrape")
def scrape_vc(vc_id: int, db: Session = Depends(get_db)):
    """Scrape a gaming VC's website for additional info."""
    vc = db.query(GamingVC).filter(GamingVC.id == vc_id).first()
    if not vc:
        raise HTTPException(status_code=404, detail="Gaming VC not found")
    result = scrape_vc_website(db, vc_id)
    return result
