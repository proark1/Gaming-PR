"""Smart matching engine endpoints — find the best contacts for your game."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.matching import AllMatchesResponse, MatchResponse
from app.services import matching_service

router = APIRouter(prefix="/api/matching", tags=["Matching"])


@router.get("/{company_id}/streamers", response_model=MatchResponse)
def match_streamers(
    company_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Find the best streamers for your game based on genre, audience, tier, and engagement."""
    try:
        matches = matching_service.match_streamers(db, company_id, limit)
        from app.models.company import CompanyProfile
        company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
        return MatchResponse(
            company_id=company_id,
            company_name=company.name if company else "",
            matches=matches,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{company_id}/investors", response_model=MatchResponse)
def match_investors(
    company_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Find the best investors for your game based on stage, focus, check size, and region."""
    try:
        matches = matching_service.match_investors(db, company_id, limit)
        from app.models.company import CompanyProfile
        company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
        return MatchResponse(
            company_id=company_id,
            company_name=company.name if company else "",
            matches=matches,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{company_id}/outlets", response_model=MatchResponse)
def match_outlets(
    company_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Find the best PR outlets for your game based on language, region, and reach."""
    try:
        matches = matching_service.match_outlets(db, company_id, limit)
        from app.models.company import CompanyProfile
        company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
        return MatchResponse(
            company_id=company_id,
            company_name=company.name if company else "",
            matches=matches,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{company_id}/all", response_model=AllMatchesResponse)
def match_all(
    company_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get top recommendations across all contact types in one call."""
    try:
        return matching_service.get_recommendations(db, company_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
