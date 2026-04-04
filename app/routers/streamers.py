from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.streamer import Streamer
from app.services.profile_service import save_streamer_profile
from app.schemas.streamer import (
    StreamerCreate,
    StreamerUpdate,
    StreamerResponse,
    StreamerDiscoverTwitchRequest,
    StreamerDiscoverYouTubeRequest,
    StreamerDiscoverCategoryRequest,
    StreamerDiscoverYouTubeSearchRequest,
    StreamerDiscoverKickRequest,
    StreamerDiscoverRumbleRequest,
    StreamerDiscoverTikTokRequest,
    StreamerDiscoverAllRequest,
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


@router.get("/leaderboard")
def leaderboard(
    tier: Optional[str] = Query(None, description="Filter by tier: bronze,silver,gold,platinum,diamond"),
    platform: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Top streamers ranked by influence score with tier badges and CPM estimates."""
    q = db.query(Streamer).filter(Streamer.is_active.is_(True))
    if tier:
        q = q.filter(Streamer.influence_tier == tier.lower())
    if platform:
        q = q.filter(Streamer.primary_platform == platform.lower())
    streamers = (
        q.order_by(Streamer.influence_score.desc().nullslast())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id, "name": s.name, "primary_platform": s.primary_platform,
            "total_followers": s.total_followers, "influence_score": s.influence_score,
            "influence_tier": s.influence_tier, "engagement_rate": s.engagement_rate,
            "estimated_cpm_usd": s.estimated_cpm_usd,
            "sponsorship_rate_usd": s.sponsorship_rate_usd,
            "platform_count": s.platform_count,
            "profile_image_url": s.profile_image_url,
        }
        for s in streamers
    ]


@router.get("/compare")
def compare_streamers(
    ids: str = Query(..., description="Comma-separated streamer IDs (2-5)"),
    db: Session = Depends(get_db),
):
    """Compare 2-5 streamers side by side on all metrics."""
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()][:5]
    if len(id_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 streamer IDs")
    streamers = db.query(Streamer).filter(Streamer.id.in_(id_list)).all()
    return [
        {
            "id": s.id, "name": s.name, "primary_platform": s.primary_platform,
            "total_followers": s.total_followers,
            "twitch_followers": s.twitch_followers, "youtube_subscribers": s.youtube_subscribers,
            "twitch_avg_viewers": s.twitch_avg_viewers,
            "influence_score": s.influence_score, "influence_tier": s.influence_tier,
            "engagement_rate": s.engagement_rate,
            "estimated_cpm_usd": s.estimated_cpm_usd,
            "sponsorship_rate_usd": s.sponsorship_rate_usd,
            "platform_count": s.platform_count,
            "game_focus": s.game_focus, "content_types": s.content_types,
            "language": s.language, "country": s.country,
            "contact_email": s.contact_email,
            "relationship_stage": s.relationship_stage,
        }
        for s in streamers
    ]


@router.get("/{streamer_id}/history")
def streamer_history(
    streamer_id: int,
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    """Get follower/score history over time for growth analysis."""
    from app.services.scoring_service import get_growth_trend
    return get_growth_trend(db, streamer_id, days)


@router.post("/score-all")
def score_all(db: Session = Depends(get_db)):
    """Recompute influence scores for all active streamers (admin)."""
    from app.services.scoring_service import score_all_streamers
    count = score_all_streamers(db)
    return {"scored": count}


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
    save_streamer_profile(db, streamer)
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
    save_streamer_profile(db, streamer)
    return streamer


@router.post("/{streamer_id}/refresh-profile", response_model=StreamerResponse)
def refresh_streamer_profile(streamer_id: int, db: Session = Depends(get_db)):
    """Recompile and save the outreach profile from current streamer data."""
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(status_code=404, detail="Streamer not found")
    save_streamer_profile(db, streamer)
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


@router.post("/discover/category")
def discover_by_category(
    payload: StreamerDiscoverCategoryRequest,
    db: Session = Depends(get_db),
):
    """
    Discover streamers across all games in a predefined category.

    Available categories: fps, battle_royale, moba, mmorpg, survival, sports,
    fighting, racing, horror, strategy, indie, mobile, vtuber, variety, esports.

    Requires TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET environment variables.
    """
    from app.services.streamer_discovery import discover_by_category as _discover
    result = _discover(
        db,
        category=payload.category,
        limit_per_game=payload.limit_per_game,
        min_viewers=payload.min_viewers,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/discover/categories")
def list_discovery_categories():
    """List all available streamer discovery categories and their games."""
    from app.services.streamer_discovery import STREAMER_CATEGORIES
    return {
        cat: {"games": games, "game_count": len(games)}
        for cat, games in sorted(STREAMER_CATEGORIES.items())
    }


@router.post("/discover/youtube/search")
def discover_youtube_search(
    payload: StreamerDiscoverYouTubeSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Discover YouTube gaming channels by search query.

    Searches YouTube for channels matching the query and upserts them.
    No API key required.
    """
    from app.services.streamer_discovery import discover_youtube_by_search
    result = discover_youtube_by_search(
        db,
        query=payload.query,
        max_results=payload.max_results,
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


@router.post("/discover/kick")
def discover_kick(
    payload: StreamerDiscoverKickRequest,
    db: Session = Depends(get_db),
):
    """
    Discover live Kick streamers by category slug.

    Popular slugs: gaming, fortnite, valorant, call-of-duty, league-of-legends.
    No API key required.
    """
    from app.services.streamer_discovery import discover_from_kick
    result = discover_from_kick(db, category=payload.category, limit=payload.limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/discover/rumble")
def discover_rumble(
    payload: StreamerDiscoverRumbleRequest,
    db: Session = Depends(get_db),
):
    """
    Discover Rumble channels by search query.

    Searches Rumble for channels matching the query and upserts them.
    No API key required.
    """
    from app.services.streamer_discovery import discover_from_rumble
    result = discover_from_rumble(db, query=payload.query, limit=payload.limit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/discover/tiktok")
def discover_tiktok(
    payload: StreamerDiscoverTikTokRequest,
    db: Session = Depends(get_db),
):
    """
    Discover a TikTok user by username and upsert their profile.

    No API key required.
    """
    from app.services.streamer_discovery import discover_tiktok_user
    result = discover_tiktok_user(db, username=payload.username)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/discover/youtube/category")
def discover_youtube_category(
    payload: StreamerDiscoverCategoryRequest,
    db: Session = Depends(get_db),
):
    """
    Discover YouTube gaming channels by category.

    Uses the same categories as Twitch category discovery. No API key required.
    """
    from app.services.streamer_discovery import discover_youtube_by_category
    result = discover_youtube_by_category(
        db, category=payload.category, limit_per_game=payload.limit_per_game,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/discover/all")
def discover_all_platforms(
    payload: StreamerDiscoverAllRequest,
    db: Session = Depends(get_db),
):
    """
    Discover streamers across all supported platforms with a single call.

    Searches Twitch (if credentials set), YouTube, Kick, and Rumble
    for the given query. Returns combined results per platform.
    """
    from app.services.streamer_discovery import discover_all
    result = discover_all(
        db,
        query=payload.query,
        limit_per_platform=payload.limit_per_platform,
        min_viewers=payload.min_viewers,
    )
    return result


@router.get("/discover/platforms")
def list_discovery_platforms():
    """List all supported discovery platforms and their capabilities."""
    import os
    twitch_available = bool(os.getenv("TWITCH_CLIENT_ID") and os.getenv("TWITCH_CLIENT_SECRET"))
    return {
        "platforms": {
            "twitch": {
                "available": twitch_available,
                "requires_credentials": True,
                "discovery_modes": ["by_game", "by_category"],
                "note": "Set TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET env vars" if not twitch_available else "Ready",
            },
            "youtube": {
                "available": True,
                "requires_credentials": False,
                "discovery_modes": ["by_search", "by_channel_id", "by_category"],
            },
            "kick": {
                "available": True,
                "requires_credentials": False,
                "discovery_modes": ["by_category"],
            },
            "rumble": {
                "available": True,
                "requires_credentials": False,
                "discovery_modes": ["by_search"],
            },
            "tiktok": {
                "available": True,
                "requires_credentials": False,
                "discovery_modes": ["by_username"],
            },
        }
    }


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
