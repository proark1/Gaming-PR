"""
Compiles outreach profiles from structured entity fields.
No LLM required — pure data extraction saved as JSON strings.
"""
import json

from sqlalchemy.orm import Session

from app.models.outlet import GamingOutlet
from app.models.streamer import Streamer
from app.models.investor import GamingInvestor


def compile_outlet_profile(outlet: GamingOutlet) -> str:
    """Return JSON string with outreach-relevant outlet data."""
    social_links = {}
    if outlet.social_twitter:
        social_links["twitter"] = outlet.social_twitter
    if outlet.social_linkedin:
        social_links["linkedin"] = outlet.social_linkedin
    if outlet.social_youtube:
        social_links["youtube"] = outlet.social_youtube

    profile = {
        "name": outlet.name,
        "category": outlet.category or "gaming_news",
        "language": outlet.language,
        "region": outlet.region,
        "country": outlet.country,
        "description": outlet.description,
        "monthly_visitors": outlet.monthly_visitors,
        "contact_email": outlet.contact_email,
        "social_links": social_links,
        "url": outlet.url,
        "priority": outlet.priority,
    }
    return json.dumps({k: v for k, v in profile.items() if v is not None}, ensure_ascii=False)


def compile_streamer_profile(streamer: Streamer) -> str:
    """Return JSON string with outreach-relevant streamer data."""
    profile = {
        "name": streamer.name,
        "primary_platform": streamer.primary_platform,
        "language": streamer.language,
        "country": streamer.country,
        "total_followers": streamer.total_followers,
        "twitch_avg_viewers": streamer.twitch_avg_viewers,
        "twitch_followers": streamer.twitch_followers,
        "youtube_subscribers": streamer.youtube_subscribers,
        "game_focus": streamer.game_focus or [],
        "content_types": streamer.content_types or [],
        "description": streamer.description or streamer.twitch_description or streamer.youtube_description,
        "is_verified": streamer.is_verified,
        "contact_email": streamer.contact_email,
        "management_company": streamer.management_company,
        "twitch_url": streamer.twitch_url,
        "youtube_url": streamer.youtube_url,
    }
    return json.dumps({k: v for k, v in profile.items() if v is not None and v != [] and v != {}}, ensure_ascii=False)


def compile_investor_profile(investor: GamingInvestor) -> str:
    """Return JSON string with outreach-relevant investor data."""
    notable = investor.notable_portfolio or []
    # Take first 5 portfolio company names
    portfolio_names = [p.get("name") if isinstance(p, dict) else str(p) for p in notable[:5]]

    profile = {
        "name": investor.name,
        "short_name": investor.short_name,
        "investor_type": investor.investor_type,
        "focus_areas": investor.focus_areas or [],
        "investment_stages": investor.investment_stages or [],
        "typical_check_min_k": investor.typical_check_min_k,
        "typical_check_max_k": investor.typical_check_max_k,
        "headquarters_region": investor.headquarters_region,
        "headquarters_country": investor.headquarters_country,
        "headquarters_city": investor.headquarters_city,
        "notable_portfolio": portfolio_names,
        "description": investor.description,
        "contact_name": investor.contact_name,
        "contact_email": investor.contact_email,
        "website": investor.website,
        "aum_millions": investor.aum_millions,
        "is_gaming_focused": investor.is_gaming_focused,
    }
    return json.dumps({k: v for k, v in profile.items() if v is not None and v != [] and v != {}}, ensure_ascii=False)


def save_outlet_profile(db: Session, outlet: GamingOutlet) -> None:
    """Compile and save outreach_profile on the outlet record."""
    outlet.outreach_profile = compile_outlet_profile(outlet)
    db.add(outlet)
    db.commit()
    db.refresh(outlet)


def save_streamer_profile(db: Session, streamer: Streamer) -> None:
    """Compile and save outreach_profile on the streamer record."""
    streamer.outreach_profile = compile_streamer_profile(streamer)
    db.add(streamer)
    db.commit()
    db.refresh(streamer)


def save_investor_profile(db: Session, investor: GamingInvestor) -> None:
    """Compile and save outreach_profile on the investor record."""
    investor.outreach_profile = compile_investor_profile(investor)
    db.add(investor)
    db.commit()
    db.refresh(investor)
