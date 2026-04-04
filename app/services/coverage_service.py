"""
Press Coverage Monitor — track and value media mentions.

Auto-detects coverage from scraped articles, computes earned media value (EMV),
and links coverage to campaigns for ROI attribution.
"""
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.company import CompanyProfile
from app.models.coverage import PressCoverage
from app.models.outlet import GamingOutlet
from app.models.scraped_article import ScrapedArticle

logger = logging.getLogger(__name__)

# CPM by coverage type ($ per 1000 impressions equivalent)
CPM_BY_TYPE = {
    "feature": 25.0,
    "review": 20.0,
    "interview": 30.0,
    "news_mention": 10.0,
    "list": 8.0,
    "sponsored": 5.0,
}

# Prominence multiplier
PROMINENCE_MULT = {
    "headline": 3.0,
    "featured": 2.0,
    "mentioned": 1.0,
    "brief": 0.5,
}


def compute_emv(reach: int, coverage_type: str, prominence: str) -> float:
    """Compute estimated media value: reach × CPM × prominence."""
    cpm = CPM_BY_TYPE.get(coverage_type, 10.0)
    mult = PROMINENCE_MULT.get(prominence, 1.0)
    return round((reach / 1000) * cpm * mult, 2)


def add_coverage(db: Session, data: dict) -> PressCoverage:
    """Manually add a press coverage entry."""
    # Compute reach from outlet if available
    reach = 0
    if data.get("outlet_id"):
        outlet = db.query(GamingOutlet).filter(GamingOutlet.id == data["outlet_id"]).first()
        if outlet:
            reach = outlet.monthly_visitors or 0

    emv = compute_emv(reach, data.get("coverage_type", "news_mention"), data.get("prominence", "mentioned"))

    coverage = PressCoverage(
        company_id=data["company_id"],
        outlet_id=data.get("outlet_id"),
        outlet_name=data["outlet_name"],
        article_url=data["article_url"],
        article_title=data["article_title"],
        coverage_type=data.get("coverage_type", "news_mention"),
        sentiment=data.get("sentiment", "neutral"),
        prominence=data.get("prominence", "mentioned"),
        estimated_reach=reach,
        estimated_media_value_usd=emv,
        excerpt=data.get("excerpt"),
        rating_score=data.get("rating_score"),
        rating_max=data.get("rating_max"),
        published_at=data.get("published_at"),
        source_campaign_id=data.get("source_campaign_id"),
    )
    db.add(coverage)
    db.commit()
    db.refresh(coverage)
    return coverage


def auto_detect_coverage(db: Session, company_id: int) -> list[PressCoverage]:
    """Scan scraped articles for mentions of the company/game name."""
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")

    # Build search terms from company name
    search_terms = [company.name.lower()]
    if company.genre:
        # Don't search by genre alone — too broad
        pass

    # Find matching articles not already tracked
    existing_urls = set(
        url for (url,) in db.query(PressCoverage.article_url)
        .filter(PressCoverage.company_id == company_id).all()
    )

    articles = db.query(ScrapedArticle).filter(
        ScrapedArticle.is_active.is_(True),
    ).all()

    detected = []
    for article in articles:
        if article.url in existing_urls:
            continue

        title_lower = (article.title or "").lower()
        content_lower = (article.content_full_text or "").lower()

        matched = any(term in title_lower or term in content_lower for term in search_terms)
        if not matched:
            continue

        # Determine prominence
        prominence = "brief"
        if any(term in title_lower for term in search_terms):
            prominence = "headline"
        elif content_lower.count(search_terms[0]) >= 3:
            prominence = "featured"
        else:
            prominence = "mentioned"

        # Get outlet info
        outlet = None
        outlet_name = "Unknown"
        reach = 0
        if article.outlet_id:
            outlet = db.query(GamingOutlet).filter(GamingOutlet.id == article.outlet_id).first()
            if outlet:
                outlet_name = outlet.name
                reach = outlet.monthly_visitors or 0

        emv = compute_emv(reach, "news_mention", prominence)

        coverage = PressCoverage(
            company_id=company_id,
            outlet_id=article.outlet_id,
            outlet_name=outlet_name,
            article_url=article.url,
            article_title=article.title or "",
            scraped_article_id=article.id,
            coverage_type="news_mention",
            sentiment="neutral",
            prominence=prominence,
            estimated_reach=reach,
            estimated_media_value_usd=emv,
            excerpt=(article.description or "")[:500],
            published_at=article.published_at,
        )
        db.add(coverage)
        detected.append(coverage)

    if detected:
        db.commit()
        for c in detected:
            db.refresh(c)

    logger.info("Auto-detected %d coverage entries for company %d", len(detected), company_id)
    return detected


def list_coverage(
    db: Session,
    company_id: int,
    coverage_type: str = None,
    sentiment: str = None,
    limit: int = 50,
    offset: int = 0,
) -> list[PressCoverage]:
    """List coverage entries with filters."""
    q = db.query(PressCoverage).filter(PressCoverage.company_id == company_id)
    if coverage_type:
        q = q.filter(PressCoverage.coverage_type == coverage_type)
    if sentiment:
        q = q.filter(PressCoverage.sentiment == sentiment)
    return q.order_by(PressCoverage.published_at.desc().nullslast()).offset(offset).limit(limit).all()


def get_coverage_summary(db: Session, company_id: int) -> dict:
    """Aggregate coverage stats and EMV."""
    entries = db.query(PressCoverage).filter(PressCoverage.company_id == company_id).all()

    by_type = defaultdict(int)
    by_sentiment = defaultdict(int)
    by_outlet = defaultdict(lambda: {"count": 0, "emv": 0})
    total_reach = 0
    total_emv = 0.0

    for c in entries:
        by_type[c.coverage_type] += 1
        by_sentiment[c.sentiment] += 1
        by_outlet[c.outlet_name]["count"] += 1
        by_outlet[c.outlet_name]["emv"] += c.estimated_media_value_usd or 0
        total_reach += c.estimated_reach or 0
        total_emv += c.estimated_media_value_usd or 0

    outlet_list = sorted(
        [{"outlet_name": k, **v} for k, v in by_outlet.items()],
        key=lambda x: x["emv"],
        reverse=True,
    )

    return {
        "total_articles": len(entries),
        "total_reach": total_reach,
        "total_emv": round(total_emv, 2),
        "by_type": dict(by_type),
        "by_sentiment": dict(by_sentiment),
        "by_outlet": outlet_list[:20],
    }
