"""Press coverage monitoring endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.coverage import CoverageCreate, CoverageResponse, CoverageSummary, CoverageUpdate
from app.services import coverage_service

router = APIRouter(prefix="/api/coverage", tags=["Coverage"])


@router.post("/", response_model=CoverageResponse, status_code=201)
def add_coverage(payload: CoverageCreate, db: Session = Depends(get_db)):
    """Manually add a press coverage entry."""
    try:
        return coverage_service.add_coverage(db, payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auto-detect", response_model=list[CoverageResponse])
def auto_detect(company_id: int, db: Session = Depends(get_db)):
    """Scan scraped articles for mentions of the company/game."""
    try:
        return coverage_service.auto_detect_coverage(db, company_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=list[CoverageResponse])
def list_coverage(
    company_id: int,
    coverage_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List coverage entries with filters."""
    return coverage_service.list_coverage(db, company_id, coverage_type, sentiment, limit, offset)


@router.get("/summary", response_model=CoverageSummary)
def coverage_summary(company_id: int, db: Session = Depends(get_db)):
    """Aggregate coverage stats and earned media value."""
    return coverage_service.get_coverage_summary(db, company_id)


@router.put("/{coverage_id}", response_model=CoverageResponse)
def update_coverage(
    coverage_id: int,
    payload: CoverageUpdate,
    db: Session = Depends(get_db),
):
    """Update a coverage entry."""
    from app.models.coverage import PressCoverage
    coverage = db.query(PressCoverage).filter(PressCoverage.id == coverage_id).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(coverage, field, value)
    # Recompute EMV if type or prominence changed
    if payload.coverage_type or payload.prominence:
        coverage.estimated_media_value_usd = coverage_service.compute_emv(
            coverage.estimated_reach or 0,
            coverage.coverage_type,
            coverage.prominence,
        )
    db.commit()
    db.refresh(coverage)
    return coverage


@router.delete("/{coverage_id}")
def delete_coverage(coverage_id: int, db: Session = Depends(get_db)):
    """Delete a coverage entry."""
    from app.models.coverage import PressCoverage
    coverage = db.query(PressCoverage).filter(PressCoverage.id == coverage_id).first()
    if not coverage:
        raise HTTPException(status_code=404, detail="Coverage not found")
    db.delete(coverage)
    db.commit()
    return {"deleted": True}
