"""
Smart matching engine — scores contacts against a company profile
to find the best streamers, investors, and outlets for outreach.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.company import CompanyProfile
from app.models.investor import GamingInvestor
from app.models.outlet import GamingOutlet
from app.models.streamer import Streamer

logger = logging.getLogger(__name__)

# Genre → game_focus keyword mapping for streamer matching
GENRE_KEYWORDS = {
    "fps": ["FPS", "Valorant", "Counter-Strike", "Call of Duty", "Overwatch", "Apex Legends", "Fortnite"],
    "rpg": ["RPG", "Elden Ring", "Final Fantasy", "Baldur's Gate", "Diablo", "Genshin Impact"],
    "moba": ["MOBA", "League of Legends", "Dota 2", "Smite"],
    "battle_royale": ["Battle Royale", "Fortnite", "PUBG", "Apex Legends", "Warzone"],
    "mmorpg": ["MMO", "MMORPG", "World of Warcraft", "FFXIV", "Lost Ark"],
    "sports": ["Sports", "FIFA", "NBA 2K", "Madden", "F1"],
    "racing": ["Racing", "Forza", "Gran Turismo", "F1"],
    "strategy": ["Strategy", "Civilization", "Age of Empires", "Total War", "StarCraft"],
    "horror": ["Horror", "Resident Evil", "Dead by Daylight", "Phasmophobia"],
    "survival": ["Survival", "Minecraft", "Rust", "DayZ", "Valheim"],
    "simulation": ["Simulation", "Simulator", "Cities: Skylines", "Stardew Valley"],
    "fighting": ["Fighting", "FGC", "Street Fighter", "Tekken", "Mortal Kombat"],
    "indie": ["Indie", "Variety"],
    "mobile": ["Mobile", "Clash Royale", "PUBG Mobile"],
}

# Funding stage → investment stage mapping
FUNDING_STAGE_MAP = {
    "bootstrapped": [],
    "pre_seed": ["pre_seed"],
    "seed": ["seed", "pre_seed"],
    "series_a": ["series_a", "seed"],
    "series_b": ["series_b", "series_a"],
    "growth": ["growth", "late_stage", "series_b"],
}


def _overlap_score(list_a: list, list_b: list) -> float:
    """Score overlap between two lists (0.0-1.0). Case-insensitive."""
    if not list_a or not list_b:
        return 0.0
    set_a = {str(x).lower() for x in list_a}
    set_b = {str(x).lower() for x in list_b}
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def _genre_matches_focus(genres: list, game_focus: list) -> float:
    """Check if company genres align with streamer's game focus."""
    if not genres or not game_focus:
        return 0.0
    focus_lower = [g.lower() for g in game_focus]
    matches = 0
    total_keywords = 0
    for genre in genres:
        keywords = GENRE_KEYWORDS.get(genre.lower(), [genre])
        total_keywords += len(keywords)
        for kw in keywords:
            if any(kw.lower() in f for f in focus_lower):
                matches += 1
    return min(matches / max(total_keywords, 1), 1.0)


def match_streamers(
    db: Session, company_id: int, limit: int = 20,
) -> list[dict]:
    """
    Score streamers against company profile.

    Weights: genre_match=30%, region=20%, tier=20%, engagement=15%, platform=15%
    """
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")

    streamers = db.query(Streamer).filter(Streamer.is_active.is_(True)).all()
    results = []

    for s in streamers:
        reasons = []
        weak = []

        # Genre match (0-30)
        genre_score = _genre_matches_focus(company.genre or [], s.game_focus or []) * 30
        if genre_score > 15:
            reasons.append(f"genre_match:{','.join(company.genre or [])}")
        elif genre_score < 5:
            weak.append("genre_mismatch")

        # Region match (0-20)
        pref_regions = company.preferred_regions or []
        streamer_region = s.region or ""
        if pref_regions and streamer_region:
            region_score = 20.0 if streamer_region.upper() in [r.upper() for r in pref_regions] else 0.0
            if region_score > 0:
                reasons.append(f"region:{streamer_region}")
            else:
                weak.append(f"region:{streamer_region}_not_preferred")
        else:
            region_score = 10.0  # neutral if no preference set

        # Tier match (0-20)
        pref_tiers = company.preferred_streamer_tiers or []
        streamer_tier = getattr(s, "influence_tier", None) or "bronze"
        if pref_tiers:
            tier_score = 20.0 if streamer_tier in [t.lower() for t in pref_tiers] else 5.0
            if tier_score > 5:
                reasons.append(f"tier:{streamer_tier}")
        else:
            # Default: prefer higher tiers
            tier_map = {"diamond": 20, "platinum": 16, "gold": 12, "silver": 8, "bronze": 4}
            tier_score = tier_map.get(streamer_tier, 4)

        # Engagement (0-15)
        engagement = getattr(s, "engagement_rate", None) or 0.0
        engagement_score = min(engagement / 0.10, 1.0) * 15
        if engagement > 0.05:
            reasons.append(f"engagement:{engagement:.1%}")

        # Platform match (0-15)
        pref_platforms = company.preferred_platforms or []
        streamer_platform = (s.primary_platform or "").lower()
        if pref_platforms:
            platform_score = 15.0 if streamer_platform in [p.lower() for p in pref_platforms] else 3.0
            if platform_score > 3:
                reasons.append(f"platform:{streamer_platform}")
            else:
                weak.append(f"platform:{streamer_platform}_not_preferred")
        else:
            platform_score = 10.0

        # Historical engagement bonus (0-10)
        try:
            from app.services.engagement_scoring_service import get_engagement_score
            hist_score = get_engagement_score(db, "streamer", s.id) / 100.0 * 10
            if hist_score > 7:
                reasons.append("historically_responsive")
            elif hist_score < 3:
                weak.append("low_historical_response")
        except Exception:
            hist_score = 5.0  # neutral

        total = genre_score + region_score + tier_score + engagement_score + platform_score + hist_score
        results.append({
            "target_type": "streamer",
            "target_id": s.id,
            "target_name": s.name,
            "match_score": round(min(total, 100), 1),
            "match_reasons": reasons,
            "weak_points": weak,
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:limit]


def match_investors(
    db: Session, company_id: int, limit: int = 20,
) -> list[dict]:
    """
    Score investors against company profile.

    Weights: stage=30%, focus=25%, check_size=20%, region=15%, gaming_focus=10%
    """
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")

    investors = db.query(GamingInvestor).filter(GamingInvestor.is_active.is_(True)).all()
    results = []

    target_stages = FUNDING_STAGE_MAP.get(company.funding_stage or "", [])

    for inv in investors:
        reasons = []
        weak = []

        # Stage match (0-30)
        inv_stages = inv.investment_stages or []
        if target_stages and inv_stages:
            stage_overlap = _overlap_score(target_stages, inv_stages)
            stage_score = stage_overlap * 30
            if stage_overlap > 0:
                reasons.append(f"stage_match:{company.funding_stage}")
            else:
                weak.append("stage_mismatch")
        else:
            stage_score = 15.0

        # Focus area match (0-25)
        inv_focus = inv.focus_areas or []
        company_genres = company.genre or []
        # Map genres to investor focus areas
        genre_to_focus = {
            "mobile": "mobile_gaming", "mmorpg": "game_studios", "fps": "esports",
            "moba": "esports", "battle_royale": "esports",
        }
        mapped_focus = [genre_to_focus.get(g, "game_studios") for g in company_genres]
        mapped_focus.append("game_studios")  # always relevant
        focus_overlap = _overlap_score(mapped_focus, inv_focus)
        focus_score = focus_overlap * 25
        if focus_overlap > 0:
            reasons.append(f"focus:{','.join(inv_focus[:2])}")

        # Check size match (0-20)
        target_k = company.funding_target_k or 0
        min_k = inv.typical_check_min_k or 0
        max_k = inv.typical_check_max_k or float("inf")
        if target_k > 0 and (min_k > 0 or max_k < float("inf")):
            if min_k <= target_k <= max_k:
                check_score = 20.0
                reasons.append(f"check_size_fit:${min_k}K-${max_k}K")
            elif target_k < min_k:
                check_score = max(0, 10 - (min_k - target_k) / min_k * 10) if min_k else 10
                weak.append("raise_below_min_check")
            else:
                check_score = max(0, 10 - (target_k - max_k) / max_k * 10) if max_k else 10
                weak.append("raise_above_max_check")
        else:
            check_score = 10.0

        # Region match (0-15)
        pref_regions = company.preferred_regions or []
        inv_region = inv.headquarters_region or ""
        if pref_regions and inv_region:
            region_score = 15.0 if inv_region.upper() in [r.upper() for r in pref_regions] else 5.0
            if region_score > 5:
                reasons.append(f"region:{inv_region}")
        else:
            region_score = 8.0

        # Gaming focus (0-10)
        gaming_score = 10.0 if inv.is_gaming_focused else 3.0
        if inv.is_gaming_focused:
            reasons.append("gaming_focused")

        # Historical engagement bonus (0-10)
        try:
            from app.services.engagement_scoring_service import get_engagement_score
            hist_score = get_engagement_score(db, "vc", inv.id) / 100.0 * 10
            if hist_score > 7:
                reasons.append("historically_responsive")
            elif hist_score < 3:
                weak.append("low_historical_response")
        except Exception:
            hist_score = 5.0

        total = stage_score + focus_score + check_score + region_score + gaming_score + hist_score
        results.append({
            "target_type": "investor",
            "target_id": inv.id,
            "target_name": inv.name,
            "match_score": round(min(total, 100), 1),
            "match_reasons": reasons,
            "weak_points": weak,
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:limit]


def match_outlets(
    db: Session, company_id: int, limit: int = 20,
) -> list[dict]:
    """
    Score outlets against company profile.

    Weights: language=30%, region=25%, category=25%, priority/reach=20%
    """
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")

    outlets = db.query(GamingOutlet).filter(GamingOutlet.is_active.is_(True)).all()
    results = []

    for o in outlets:
        reasons = []
        weak = []

        # Language match (0-30)
        pref_regions = company.preferred_regions or []
        outlet_lang = o.language or ""
        # Simple: English outlets match any, others need region alignment
        if outlet_lang == "en":
            lang_score = 25.0
            reasons.append("language:en")
        elif pref_regions:
            lang_score = 15.0  # partial credit for any outlet
        else:
            lang_score = 20.0

        # Region match (0-25)
        outlet_region = o.region or ""
        if pref_regions and outlet_region:
            region_score = 25.0 if outlet_region.upper() in [r.upper() for r in pref_regions] else 5.0
            if region_score > 5:
                reasons.append(f"region:{outlet_region}")
        else:
            region_score = 12.0

        # Category match (0-25)
        cat = o.category or ""
        if "gaming" in cat.lower():
            cat_score = 25.0
            reasons.append(f"category:{cat}")
        else:
            cat_score = 10.0

        # Priority/reach (0-20)
        priority = o.priority or 5
        visitors = o.monthly_visitors or 0
        priority_score = max(0, (11 - priority) / 10.0) * 12  # priority 1 = 12, 10 = 1.2
        if visitors > 1_000_000:
            priority_score += 8
            reasons.append("high_reach")
        elif visitors > 100_000:
            priority_score += 5
        priority_score = min(priority_score, 20)

        # Historical engagement bonus (0-10)
        try:
            from app.services.engagement_scoring_service import get_engagement_score
            hist_score = get_engagement_score(db, "outlet", o.id) / 100.0 * 10
            if hist_score > 7:
                reasons.append("historically_responsive")
            elif hist_score < 3:
                weak.append("low_historical_response")
        except Exception:
            hist_score = 5.0

        total = lang_score + region_score + cat_score + priority_score + hist_score
        results.append({
            "target_type": "outlet",
            "target_id": o.id,
            "target_name": o.name,
            "match_score": round(min(total, 100), 1),
            "match_reasons": reasons,
            "weak_points": weak,
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:limit]


def get_recommendations(
    db: Session, company_id: int, limit: int = 10,
) -> dict:
    """Get top matches for each contact type."""
    company = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()
    if not company:
        raise ValueError(f"Company {company_id} not found")

    return {
        "company_id": company.id,
        "company_name": company.name,
        "streamers": match_streamers(db, company_id, limit),
        "investors": match_investors(db, company_id, limit),
        "outlets": match_outlets(db, company_id, limit),
    }
