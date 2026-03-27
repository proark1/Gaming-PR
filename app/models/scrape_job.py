from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("gaming_outlets.id"), nullable=True, index=True)

    # Job info
    job_type = Column(String(50), nullable=False, default="manual")  # manual, scheduled, single
    status = Column(String(50), nullable=False, default="running", index=True)  # running, completed, failed, partial

    # Timing
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Results
    total_outlets_scraped = Column(Integer, default=0)
    total_articles_found = Column(Integer, default=0)
    total_new_articles = Column(Integer, default=0)
    total_articles_updated = Column(Integer, default=0)
    total_full_content_extracted = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)

    # Detailed results per outlet
    outlet_results = Column(JSON, nullable=True, default=list)
    errors = Column(JSON, nullable=True, default=list)

    outlet = relationship("GamingOutlet", back_populates="scrape_jobs")
