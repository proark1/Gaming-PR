from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.streamer import Streamer
from app.schemas.streamer import StreamerCreate, StreamerUpdate, StreamerResponse, StreamerStatsResponse
from app.services.contact_scraper import scrape_streamer_website

router = APIRouter(prefix="/api/streamers", tags=["streamers"])


@router.get("/", response_model=list[StreamerResponse])
def list_streamers(
    platform: Optional[str] = None,
    tier: Optional[str] = None,
    language: Optional[str] = None,
    is_active: Optional[bool] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Streamer)
    if platform:
        query = query.filter(Streamer.platform == platform)
    if tier:
        query = query.filter(Streamer.tier == tier)
    if language:
        query = query.filter(Streamer.language == language)
    if is_active is not None:
        query = query.filter(Streamer.is_active == is_active)
    if category:
        query = query.filter(Streamer.category == category)
    if search:
        query = query.filter(Streamer.name.ilike(f"%{search}%"))
    return query.order_by(Streamer.priority.asc(), Streamer.follower_count.desc().nullslast()).all()


@router.get("/stats", response_model=StreamerStatsResponse)
def streamer_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Streamer.id)).scalar()
    active = db.query(func.count(Streamer.id)).filter(Streamer.is_active.is_(True)).scalar()
    by_platform = dict(
        db.query(Streamer.platform, func.count(Streamer.id))
        .group_by(Streamer.platform)
        .all()
    )
    by_tier = dict(
        db.query(Streamer.tier, func.count(Streamer.id))
        .filter(Streamer.tier.isnot(None))
        .group_by(Streamer.tier)
        .all()
    )
    by_language = dict(
        db.query(Streamer.language, func.count(Streamer.id))
        .group_by(Streamer.language)
        .all()
    )
    total_followers = db.query(func.coalesce(func.sum(Streamer.follower_count), 0)).scalar()

    return StreamerStatsResponse(
        total_streamers=total,
        active_streamers=active,
        streamers_by_platform=by_platform,
        streamers_by_tier=by_tier,
        streamers_by_language=by_language,
        total_combined_followers=total_followers,
    )


@router.get("/{streamer_id}", response_model=StreamerResponse)
def get_streamer(streamer_id: int, db: Session = Depends(get_db)):
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")
    return streamer


@router.post("/", response_model=StreamerResponse, status_code=201)
def create_streamer(data: StreamerCreate, db: Session = Depends(get_db)):
    existing = db.query(Streamer).filter(Streamer.url == data.url).first()
    if existing:
        raise HTTPException(status_code=409, detail="Streamer with this URL already exists")
    streamer = Streamer(**data.model_dump())
    db.add(streamer)
    db.commit()
    db.refresh(streamer)
    return streamer


@router.patch("/{streamer_id}", response_model=StreamerResponse)
def update_streamer(streamer_id: int, data: StreamerUpdate, db: Session = Depends(get_db)):
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(streamer, field, value)
    db.commit()
    db.refresh(streamer)
    return streamer


@router.delete("/{streamer_id}", status_code=204)
def delete_streamer(streamer_id: int, db: Session = Depends(get_db)):
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")
    db.delete(streamer)
    db.commit()


@router.post("/{streamer_id}/scrape")
def scrape_streamer(streamer_id: int, db: Session = Depends(get_db)):
    """Scrape a streamer's website for additional info."""
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")
    result = scrape_streamer_website(db, streamer_id)
    return result
