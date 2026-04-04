"""Campaign analytics endpoints — deep insights and performance data."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/send-times")
def send_time_analysis(db: Session = Depends(get_db)):
    """Analyze best send times based on open/click patterns."""
    return analytics_service.get_send_time_analysis(db)


@router.get("/segments")
def segment_engagement(
    campaign_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Engagement breakdown by tier, platform, region, and target type."""
    return analytics_service.get_engagement_by_segment(db, campaign_id)


class CompareRequest(BaseModel):
    campaign_ids: list[int]


@router.post("/compare")
def compare_campaigns(
    payload: CompareRequest,
    db: Session = Depends(get_db),
):
    """Compare multiple campaigns side-by-side."""
    if len(payload.campaign_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 campaign IDs")
    return {"campaigns": analytics_service.compare_campaigns(db, payload.campaign_ids)}


@router.get("/funnel/{campaign_id}")
def funnel_analysis(campaign_id: int, db: Session = Depends(get_db)):
    """Step-by-step dropoff funnel for a campaign."""
    try:
        return analytics_service.get_funnel_analysis(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/top-responders")
def top_responders(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    """Contacts with highest response rates."""
    return analytics_service.get_top_responders(db, limit)


@router.get("/trends")
def performance_trends(
    days: int = Query(90, le=365),
    db: Session = Depends(get_db),
):
    """Weekly performance trends over time."""
    return {"periods": analytics_service.get_performance_trends(db, days)}


@router.get("/summary")
def analytics_summary(db: Session = Depends(get_db)):
    """High-level analytics dashboard summary."""
    return analytics_service.get_analytics_summary(db)
