from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.streamer import Streamer
from app.schemas.streamer import (
    StreamerCreate,
    StreamerUpdate,
    StreamerResponse,
    StreamerDiscoverTwitchRequest,
    StreamerDiscoverYouTubeRequest,
    StreamerRefreshResponse,
)

router = APIRouter(prefix="/api/streamers", tags=["streamers"])


@router.get("/", response_model=list[StreamerResponse])
def list_streamers(
    platform: Optional[str] = Query(None, description="Filter by primary_platform: twitch, youtube, x"),
    language: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    min_followers: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    game: Optional[str] = Query(None, description="Filter by game in game_focus JSON array"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Streamer)
    if platform:
        q = q.filter(Streamer.primary_platform == platform)
    if language:
        q = q.filter(Streamer.language == language)
    if region:
        q = q.filter(Streamer.region == region.upper())
    if is_active is not None:
        q = q.filter(Streamer.is_active == is_active)
    if min_followers is not None:
        q = q.filter(Streamer.total_followers >= min_followers)
    if game:
        q = q.filter(
            func.cast(Streamer.game_focus, func.text()).contains(game)
        )
    return (
        q.order_by(Streamer.total_followers.desc().nullslast())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/stats")
def streamer_stats(db: Session = Depends(get_db)):
    from sqlalchemy import case
    row = db.query(
        func.count(Streamer.id).label("total"),
        func.sum(case((Streamer.is_active == True, 1), else_=0)).label("active"),
        func.sum(case((Streamer.twitch_username.isnot(None), 1), else_=0)).label("on_twitch"),
        func.sum(case((Streamer.youtube_channel_id.isnot(None), 1), else_=0)).label("on_youtube"),
        func.sum(case((Streamer.x_username.isnot(None), 1), else_=0)).label("on_x"),
    ).one()

    by_platform = dict(
        db.query(Streamer.primary_platform, func.count(Streamer.id))
        .group_by(Streamer.primary_platform)
        .all()
    )
    by_region = dict(
        db.query(Streamer.region, func.count(Streamer.id))
        .filter(Streamer.region.isnot(None))
        .group_by(Streamer.region)
        .all()
    )
    return {
        "total": row.total or 0,
        "active": row.active or 0,
        "on_twitch": row.on_twitch or 0,
        "on_youtube": row.on_youtube or 0,
        "on_x": row.on_x or 0,
        "by_platform": by_platform,
        "by_region": by_region,
    }


@router.get("/{streamer_id}", response_model=StreamerResponse)
def get_streamer(streamer_id: int, db: Session = Depends(get_db)):
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")
    return streamer


@router.post("/", response_model=StreamerResponse, status_code=201)
def create_streamer(payload: StreamerCreate, db: Session = Depends(get_db)):
    # Duplicate check on any unique platform handle
    if payload.twitch_username:
        if db.query(Streamer).filter(Streamer.twitch_username == payload.twitch_username).first():
            raise HTTPException(status_code=409, detail=f"Twitch username '{payload.twitch_username}' already exists")
    if payload.youtube_channel_id:
        if db.query(Streamer).filter(Streamer.youtube_channel_id == payload.youtube_channel_id).first():
            raise HTTPException(status_code=409, detail=f"YouTube channel '{payload.youtube_channel_id}' already exists")
    if payload.x_username:
        if db.query(Streamer).filter(Streamer.x_username == payload.x_username).first():
            raise HTTPException(status_code=409, detail=f"X username '{payload.x_username}' already exists")

    streamer = Streamer(**payload.model_dump())
    db.add(streamer)
    db.commit()
    db.refresh(streamer)
    return streamer


@router.put("/{streamer_id}", response_model=StreamerResponse)
def update_streamer(streamer_id: int, payload: StreamerUpdate, db: Session = Depends(get_db)):
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
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


# ---------------------------------------------------------------------------
# Discovery endpoints
# ---------------------------------------------------------------------------

@router.post("/discover/twitch")
def discover_twitch(
    payload: StreamerDiscoverTwitchRequest,
    db: Session = Depends(get_db),
):
    """
    Discover top live Twitch streamers for a given game and upsert them.

    Requires TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET environment variables.
    """
    from app.services.streamer_discovery import discover_from_twitch
    result = discover_from_twitch(
        db,
        game_name=payload.game_name,
        limit=payload.limit,
        min_viewers=payload.min_viewers,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/discover/youtube")
def discover_youtube(
    payload: StreamerDiscoverYouTubeRequest,
    db: Session = Depends(get_db),
):
    """
    Fetch and upsert a YouTube channel by its channel ID.

    Example channel IDs: UC-lHJZR3Gqxm24_Vd_AJ5Yw (PewDiePie)
    """
    from app.services.streamer_discovery import discover_youtube_channel
    result = discover_youtube_channel(db, channel_id=payload.channel_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{streamer_id}/refresh", response_model=StreamerRefreshResponse)
def refresh_streamer(streamer_id: int, db: Session = Depends(get_db)):
    """
    Re-fetch live stats for all platforms linked to a streamer
    (Twitch followers, YouTube subscribers, X followers).
    """
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")

    from app.services.streamer_discovery import refresh_streamer as _refresh
    updated_fields = _refresh(db, streamer)
    return StreamerRefreshResponse(
        streamer_id=streamer_id,
        updated_fields=updated_fields,
        message=f"Updated {len(updated_fields)} fields" if updated_fields else "No new data retrieved",
    )
