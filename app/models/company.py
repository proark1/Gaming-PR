"""Company/game profile — represents what the user is pitching to streamers, outlets, and investors."""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey

from app.database import Base


class CompanyProfile(Base):
    """
    A game studio or game being pitched for PR, streamer sponsorship, or investment.
    Links to a user and drives the matching engine for finding ideal contacts.
    """
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Basic info
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(2048), nullable=True)
    logo_url = Column(String(2048), nullable=True)

    # Game details
    genre = Column(JSON, nullable=True, default=list)  # ["fps","rpg","moba"]
    platforms = Column(JSON, nullable=True, default=list)  # ["pc","ps5","xbox","mobile","switch"]
    release_stage = Column(String(30), nullable=True)
    # concept / prototype / alpha / beta / early_access / launched
    target_audience = Column(JSON, nullable=True, default=list)
    # ["casual","competitive","streaming_friendly"]

    # Business
    funding_stage = Column(String(30), nullable=True)
    # bootstrapped / pre_seed / seed / series_a / series_b / growth
    funding_target_k = Column(Integer, nullable=True)  # target raise in $K
    marketing_budget_k = Column(Integer, nullable=True)
    team_size = Column(Integer, nullable=True)
    revenue_model = Column(String(50), nullable=True)  # f2p / premium / subscription / hybrid

    # Streamer preferences
    preferred_streamer_tiers = Column(JSON, nullable=True, default=list)  # ["gold","platinum"]
    preferred_regions = Column(JSON, nullable=True, default=list)  # ["NA","EU","APAC"]
    preferred_platforms = Column(JSON, nullable=True, default=list)  # ["twitch","youtube"]

    # Investor preferences
    preferred_investor_types = Column(JSON, nullable=True, default=list)  # ["vc","angel"]

    # Assets
    trailer_url = Column(String(2048), nullable=True)
    pitch_deck_url = Column(String(2048), nullable=True)
    media_kit_url = Column(String(2048), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
