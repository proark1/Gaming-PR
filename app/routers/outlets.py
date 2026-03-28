from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import SUPPORTED_LANGUAGES
from app.database import get_db
from app.models.outlet import GamingOutlet
from app.schemas.outlet import OutletCreate, OutletUpdate, OutletResponse, OutletStatsResponse
from app.routers.auth import get_current_user, get_admin_user

router = APIRouter(prefix="/api/outlets", tags=["outlets"])


@router.get("/", response_model=list[OutletResponse])
def list_outlets(
    language: Optional[str] = None,
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(GamingOutlet)
    if language:
        query = query.filter(GamingOutlet.language == language)
    if is_active is not None:
        query = query.filter(GamingOutlet.is_active == is_active)
    if category:
        query = query.filter(GamingOutlet.category == category)
    if search:
        query = query.filter(GamingOutlet.name.ilike(f"%{search}%"))
    return query.order_by(GamingOutlet.priority.asc(), GamingOutlet.name).all()


@router.get("/stats", response_model=OutletStatsResponse)
def outlet_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(GamingOutlet.id)).scalar()
    active = db.query(func.count(GamingOutlet.id)).filter(GamingOutlet.is_active == True).scalar()
    by_lang = dict(
        db.query(GamingOutlet.language, func.count(GamingOutlet.id))
        .group_by(GamingOutlet.language)
        .all()
    )
    total_scraped = db.query(func.coalesce(func.sum(GamingOutlet.total_articles_scraped), 0)).scalar()
    with_failures = db.query(func.count(GamingOutlet.id)).filter(GamingOutlet.consecutive_failures > 0).scalar()

    return OutletStatsResponse(
        total_outlets=total,
        active_outlets=active,
        outlets_by_language=by_lang,
        total_articles_scraped=total_scraped,
        outlets_with_failures=with_failures,
    )


@router.get("/{outlet_id}", response_model=OutletResponse)
def get_outlet(outlet_id: int, db: Session = Depends(get_db)):
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    return outlet


@router.post("/", response_model=OutletResponse, status_code=201)
def create_outlet(data: OutletCreate, db: Session = Depends(get_db), _user=Depends(get_admin_user)):
    if data.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {data.language}")
    existing = db.query(GamingOutlet).filter(GamingOutlet.url == data.url).first()
    if existing:
        raise HTTPException(status_code=409, detail="Outlet with this URL already exists")
    outlet = GamingOutlet(**data.model_dump())
    db.add(outlet)
    db.commit()
    db.refresh(outlet)
    return outlet


@router.patch("/{outlet_id}", response_model=OutletResponse)
def update_outlet(outlet_id: int, data: OutletUpdate, db: Session = Depends(get_db), _user=Depends(get_admin_user)):
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(outlet, field, value)
    db.commit()
    db.refresh(outlet)
    return outlet


@router.delete("/{outlet_id}", status_code=204)
def delete_outlet(outlet_id: int, db: Session = Depends(get_db), _user=Depends(get_admin_user)):
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    db.delete(outlet)
    db.commit()
