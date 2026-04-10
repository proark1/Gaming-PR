"""
Startup database migrations.
Uses raw SQL with IF NOT EXISTS so they're safe to run on every startup.
This handles adding new columns to existing tables that create_all() can't touch.
"""
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# All new columns added to gaming_outlets in v5.0
OUTLET_COLUMN_MIGRATIONS = [
    # Editorial details
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS editor_in_chief VARCHAR(500)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS editor_email VARCHAR(500)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS editorial_focus JSON",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS content_types_accepted JSON",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS submission_guidelines_url VARCHAR(2048)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS submission_email VARCHAR(500)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS press_kit_requirements TEXT",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS typical_response_time VARCHAR(200)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS preferred_contact_method VARCHAR(100)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS press_page_url VARCHAR(2048)",
    # Audience & reach
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS alexa_rank INTEGER",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS domain_authority INTEGER",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS social_twitter_followers INTEGER",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS social_facebook_followers INTEGER",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS social_youtube_subscribers INTEGER",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS social_instagram VARCHAR(500)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS social_instagram_followers INTEGER",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS social_tiktok VARCHAR(500)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS social_discord VARCHAR(500)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS newsletter_subscribers INTEGER",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS podcast_name VARCHAR(500)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS podcast_url VARCHAR(2048)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS youtube_channel_url VARCHAR(2048)",
    # Audience demographics
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS audience_age_range VARCHAR(100)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS audience_geography JSON",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS audience_platforms JSON",
    # Coverage patterns
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS games_covered JSON",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS platforms_covered JSON",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS genres_covered JSON",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS review_scale VARCHAR(100)",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS publishes_reviews BOOLEAN",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS publishes_previews BOOLEAN",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS publishes_interviews BOOLEAN",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS publishes_features BOOLEAN",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS average_articles_per_day INTEGER",
    # Staff & contacts
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS staff_writers JSON",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS freelance_opportunities BOOLEAN",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS freelance_rate VARCHAR(200)",
    # Website scraped data
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS scraped_data JSON",
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS scrape_errors JSON",
    # Internal notes
    "ALTER TABLE gaming_outlets ADD COLUMN IF NOT EXISTS internal_notes TEXT",
]


def run_migrations(engine) -> None:
    """
    Run all pending column migrations against the live database.
    Safe to call on every startup — all statements use IF NOT EXISTS.
    """
    with engine.connect() as conn:
        for stmt in OUTLET_COLUMN_MIGRATIONS:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                logger.warning(f"Migration skipped ({e}): {stmt}")
        conn.commit()
    logger.info(f"Column migrations complete ({len(OUTLET_COLUMN_MIGRATIONS)} statements applied).")
