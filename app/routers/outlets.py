from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.outlet import GamingOutlet
from app.schemas.outlet import OutletCreate, OutletUpdate, OutletResponse

router = APIRouter(prefix="/api/outlets", tags=["outlets"])


@router.get("/", response_model=list[OutletResponse])
def list_outlets(language: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(GamingOutlet)
    if language:
        query = query.filter(GamingOutlet.language == language)
    return query.order_by(GamingOutlet.language, GamingOutlet.name).all()


@router.get("/{outlet_id}", response_model=OutletResponse)
def get_outlet(outlet_id: int, db: Session = Depends(get_db)):
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    return outlet


@router.post("/", response_model=OutletResponse, status_code=201)
def create_outlet(data: OutletCreate, db: Session = Depends(get_db)):
    existing = db.query(GamingOutlet).filter(GamingOutlet.url == data.url).first()
    if existing:
        raise HTTPException(status_code=409, detail="Outlet with this URL already exists")
    outlet = GamingOutlet(**data.model_dump())
    db.add(outlet)
    db.commit()
    db.refresh(outlet)
    return outlet


@router.patch("/{outlet_id}", response_model=OutletResponse)
def update_outlet(outlet_id: int, data: OutletUpdate, db: Session = Depends(get_db)):
    outlet = db.query(GamingOutlet).filter(GamingOutlet.id == outlet_id).first()
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(outlet, field, value)
    db.commit()
    db.refresh(outlet)
    return outlet
