"""Company/game profile management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import CompanyProfile
from app.routers.auth import get_current_user
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.post("/", response_model=CompanyResponse, status_code=201)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a company/game profile for matching and outreach."""
    company = CompanyProfile(user_id=user.id, **payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/", response_model=list[CompanyResponse])
def list_companies(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """List the current user's company profiles."""
    return (
        db.query(CompanyProfile)
        .filter(CompanyProfile.user_id == user.id)
        .order_by(CompanyProfile.created_at.desc())
        .all()
    )


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    company = db.query(CompanyProfile).filter(
        CompanyProfile.id == company_id, CompanyProfile.user_id == user.id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    company = db.query(CompanyProfile).filter(
        CompanyProfile.id == company_id, CompanyProfile.user_id == user.id,
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
