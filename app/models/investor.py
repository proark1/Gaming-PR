from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON

from app.database import Base


class GamingInvestor(Base):
    """Gaming-focused venture capital firms, PE funds, angels, and corporate investors."""
    __tablename__ = "gaming_investors"

    id = Column(Integer, primary_key=True, index=True)

    # Identity
    name = Column(String(500), nullable=False, index=True)
    short_name = Column(String(100), nullable=True)       # e.g. "a16z", "Bitkraft"
    investor_type = Column(String(50), nullable=False, default="vc")
    # Types: vc, pe, angel, corporate, accelerator, family_office, sovereign

    # About
    description = Column(Text, nullable=True)
    website = Column(String(2048), nullable=True)
    founded_year = Column(Integer, nullable=True)
    headquarters_city = Column(String(200), nullable=True)
    headquarters_country = Column(String(100), nullable=True)
    headquarters_region = Column(String(10), nullable=True)  # US, EU, ASIA, etc.

    # Investment profile
    aum_millions = Column(Float, nullable=True)             # Assets under management (USD)
    fund_size_millions = Column(Float, nullable=True)       # Latest fund size
    typical_check_min_k = Column(Integer, nullable=True)    # Min check size (thousands USD)
    typical_check_max_k = Column(Integer, nullable=True)    # Max check size (thousands USD)
    investment_stages = Column(JSON, nullable=True, default=list)
    # e.g. ["pre_seed", "seed", "series_a", "series_b", "growth", "late_stage"]
    focus_areas = Column(JSON, nullable=True, default=list)
    # e.g. ["mobile_gaming", "esports", "web3_gaming", "game_studios", "gaming_infrastructure",
    #        "vr_ar", "game_tools", "streaming", "social_gaming"]
    active_regions = Column(JSON, nullable=True, default=list)  # ["US", "EU", "APAC"]

    # Portfolio
    notable_portfolio = Column(JSON, nullable=True, default=list)
    # e.g. [{"name": "Roblox", "url": "https://roblox.com"}, ...]
    total_known_investments = Column(Integer, nullable=True)

    # Contact & social
    contact_name = Column(String(500), nullable=True)
    contact_email = Column(String(500), nullable=True)
    contact_title = Column(String(200), nullable=True)
    linkedin_url = Column(String(2048), nullable=True)
    twitter_url = Column(String(2048), nullable=True)
    crunchbase_url = Column(String(2048), nullable=True)
    pitchbook_url = Column(String(2048), nullable=True)

    # State
    is_active = Column(Boolean, default=True, index=True)
    is_gaming_focused = Column(Boolean, default=True)  # True = gaming is primary focus
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
