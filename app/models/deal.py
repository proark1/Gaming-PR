"""Deal and sponsorship tracking models."""
from datetime import datetime, date, timezone

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Float, JSON, ForeignKey, Index,
)

from app.database import Base


class Deal(Base):
    """
    Tracks investment deals and streamer sponsorships through their lifecycle.
    Links back to the campaign/pitch that generated the opportunity.
    """
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_profiles.id"), nullable=False, index=True)

    # Contact
    contact_type = Column(String(20), nullable=False)  # vc | streamer | outlet
    contact_id = Column(Integer, nullable=False)
    contact_name = Column(String(500), nullable=False)

    # Type
    deal_type = Column(String(30), nullable=False)
    # investment | sponsorship | press_partnership | review

    # Stage tracking
    stage = Column(String(30), nullable=False, default="interested")
    # Investment: interested | due_diligence | term_sheet | closing | closed_won | closed_lost
    # Sponsorship: pitched | negotiating | contracted | active | completed | cancelled
    stage_changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Financial
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    deal_value_usd = Column(Float, nullable=True)
    payment_terms = Column(String(30), nullable=True)
    # upfront | milestone | rev_share | equity

    # Documents
    contract_url = Column(String(2048), nullable=True)
    pitch_deck_url = Column(String(2048), nullable=True)
    attachments = Column(JSON, nullable=True, default=list)
    # [{name, url, type}]

    # Timeline
    expected_close_date = Column(Date, nullable=True)
    actual_close_date = Column(Date, nullable=True)

    # Source attribution
    source_campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    source_pitch_id = Column(Integer, ForeignKey("generated_pitches.id"), nullable=True)

    # Deliverables (sponsorship)
    deliverables = Column(JSON, nullable=True, default=list)
    # [{description, due_date, status, proof_url}]

    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_deal_company_stage", "company_id", "stage"),
        Index("ix_deal_contact", "contact_type", "contact_id"),
    )


class DealStageHistory(Base):
    """Audit trail of deal stage transitions."""
    __tablename__ = "deal_stage_history"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False, index=True)
    from_stage = Column(String(30), nullable=False)
    to_stage = Column(String(30), nullable=False)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
