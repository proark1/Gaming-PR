from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class GamingVC(Base):
    __tablename__ = "gaming_vcs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    url = Column(String(2048), unique=True, nullable=False)

    # Firm details
    description = Column(Text, nullable=True)
    short_description = Column(String(1000), nullable=True)
    logo_url = Column(String(2048), nullable=True)
    founded_year = Column(Integer, nullable=True)
    headquarters = Column(String(500), nullable=True)
    region = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)
    firm_type = Column(String(100), nullable=True, default="venture_capital")  # vc, angel, accelerator, corporate_vc, family_office

    # Investment focus
    investment_stage = Column(JSON, nullable=True, default=list)  # ["pre-seed", "seed", "series-a", "series-b", "growth"]
    investment_focus = Column(JSON, nullable=True, default=list)  # ["gaming", "esports", "game-tech", "metaverse", "web3-gaming"]
    gaming_subsectors = Column(JSON, nullable=True, default=list)  # ["mobile-gaming", "pc-gaming", "console", "VR/AR", "game-tools", "streaming"]
    preferred_platforms = Column(JSON, nullable=True, default=list)  # ["PC", "Mobile", "Console", "Cross-platform"]
    thesis = Column(Text, nullable=True)  # Investment thesis / philosophy

    # Financial info
    fund_size = Column(String(200), nullable=True)  # "$200M"
    total_aum = Column(String(200), nullable=True)  # Assets under management
    typical_check_size = Column(String(200), nullable=True)  # "$500K - $5M"
    min_check_size = Column(String(100), nullable=True)
    max_check_size = Column(String(100), nullable=True)
    total_investments = Column(Integer, nullable=True)
    total_exits = Column(Integer, nullable=True)

    # Portfolio
    notable_portfolio = Column(JSON, nullable=True, default=list)  # [{"name": "Epic Games", "url": "...", "status": "active"}]
    portfolio_companies_count = Column(Integer, nullable=True)
    notable_exits = Column(JSON, nullable=True, default=list)  # [{"name": "Discord", "exit_type": "IPO", "return": "50x"}]
    active_portfolio_count = Column(Integer, nullable=True)

    # Team
    partners = Column(JSON, nullable=True, default=list)  # [{"name": "John Doe", "title": "Managing Partner", "linkedin": "...", "email": "..."}]
    team_size = Column(Integer, nullable=True)
    key_decision_makers = Column(JSON, nullable=True, default=list)  # [{"name": "...", "title": "...", "focus": "gaming"}]

    # Contact info
    contact_email = Column(String(500), nullable=True)
    pitch_email = Column(String(500), nullable=True)  # Dedicated pitch/deal flow email
    pitch_form_url = Column(String(2048), nullable=True)
    phone = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)

    # Social media
    social_twitter = Column(String(500), nullable=True)
    social_linkedin = Column(String(500), nullable=True)
    social_crunchbase = Column(String(500), nullable=True)
    social_angellist = Column(String(500), nullable=True)
    social_medium = Column(String(500), nullable=True)
    twitter_followers = Column(Integer, nullable=True)
    linkedin_followers = Column(Integer, nullable=True)

    # Activity & recent news
    recent_investments = Column(JSON, nullable=True, default=list)  # [{"company": "...", "amount": "$10M", "date": "2024-01", "round": "Series A"}]
    recent_news = Column(JSON, nullable=True, default=list)  # [{"title": "...", "url": "...", "date": "..."}]
    blog_url = Column(String(2048), nullable=True)
    newsletter_url = Column(String(2048), nullable=True)
    podcast_url = Column(String(2048), nullable=True)
    events_attended = Column(JSON, nullable=True, default=list)  # ["GDC", "E3", "Gamescom"]

    # Categorization
    tier = Column(String(50), nullable=True, default="mid")  # "top-tier", "mid-tier", "emerging", "boutique"
    category = Column(String(100), nullable=True, default="gaming_vc")
    tags = Column(JSON, nullable=True, default=list)
    priority = Column(Integer, default=5)

    # Scraping state
    is_active = Column(Boolean, default=True, index=True)
    last_scraped_at = Column(DateTime, nullable=True)
    scraped_data = Column(JSON, nullable=True)
    scrape_errors = Column(JSON, nullable=True, default=list)

    # Notes
    internal_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    outreach_messages = relationship("OutreachMessage", back_populates="gaming_vc", cascade="all, delete-orphan",
                                     foreign_keys="OutreachMessage.gaming_vc_id")
