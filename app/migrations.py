"""
Startup database migrations.
Uses raw SQL with IF NOT EXISTS so they're safe to run on every startup.
This handles adding new columns to existing tables that create_all() can't touch.
"""
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# All columns for gaming_outlets (new fields added in v5.0)
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

# All columns for streamers (full list — safe to re-run with IF NOT EXISTS)
STREAMER_COLUMN_MIGRATIONS = [
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS real_name VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS platform VARCHAR(50)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS twitch_username VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS youtube_channel VARCHAR(2048)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS youtube_channel_id VARCHAR(200)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS kick_username VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS tiktok_username VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS bio TEXT",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS profile_image_url VARCHAR(2048)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS banner_image_url VARCHAR(2048)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS language VARCHAR(10)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS region VARCHAR(10)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS country VARCHAR(100)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS follower_count INTEGER",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS subscriber_count INTEGER",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS avg_viewers INTEGER",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS peak_viewers INTEGER",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS total_views INTEGER",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS avg_stream_duration_hours FLOAT",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS stream_schedule TEXT",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS is_partnered BOOLEAN DEFAULT FALSE",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS is_affiliated BOOLEAN DEFAULT FALSE",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS primary_game VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS games_played JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS content_categories JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS content_style VARCHAR(200)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS is_variety_streamer BOOLEAN DEFAULT FALSE",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS audience_age_range VARCHAR(50)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS audience_gender_split JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS audience_top_countries JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS social_twitter VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS social_instagram VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS social_discord VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS social_tiktok VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS social_youtube VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS social_facebook VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS twitter_followers INTEGER",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS instagram_followers INTEGER",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS discord_members INTEGER",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS contact_email VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS business_email VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS manager_name VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS manager_email VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS agency VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS agency_url VARCHAR(2048)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS has_sponsorships BOOLEAN DEFAULT FALSE",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS past_sponsors JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS estimated_sponsorship_rate VARCHAR(200)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS accepts_game_codes BOOLEAN",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS accepts_sponsored_streams BOOLEAN",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS has_merch_store BOOLEAN DEFAULT FALSE",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS merch_url VARCHAR(2048)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS is_esports_player BOOLEAN DEFAULT FALSE",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS esports_team VARCHAR(500)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS esports_role VARCHAR(200)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS tournament_history JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS tier VARCHAR(50)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS category VARCHAR(100)",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS tags JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 5",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS last_scraped_at TIMESTAMP",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS scraped_data JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS scrape_errors JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS notable_achievements JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS recent_milestones JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS content_highlights JSON",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS internal_notes TEXT",
    "ALTER TABLE streamers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
]

# All columns for gaming_vcs (full list — safe to re-run with IF NOT EXISTS)
VC_COLUMN_MIGRATIONS = [
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS description TEXT",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS short_description VARCHAR(1000)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS logo_url VARCHAR(2048)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS founded_year INTEGER",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS headquarters VARCHAR(500)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS region VARCHAR(10)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS country VARCHAR(100)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS firm_type VARCHAR(100)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS investment_stage JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS investment_focus JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS gaming_subsectors JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS preferred_platforms JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS thesis TEXT",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS fund_size VARCHAR(200)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS total_aum VARCHAR(200)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS typical_check_size VARCHAR(200)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS min_check_size VARCHAR(100)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS max_check_size VARCHAR(100)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS total_investments INTEGER",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS total_exits INTEGER",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS notable_portfolio JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS portfolio_companies_count INTEGER",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS notable_exits JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS active_portfolio_count INTEGER",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS partners JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS team_size INTEGER",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS key_decision_makers JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS contact_email VARCHAR(500)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS pitch_email VARCHAR(500)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS pitch_form_url VARCHAR(2048)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS phone VARCHAR(100)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS address TEXT",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS social_twitter VARCHAR(500)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS social_linkedin VARCHAR(500)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS social_crunchbase VARCHAR(500)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS social_angellist VARCHAR(500)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS social_medium VARCHAR(500)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS twitter_followers INTEGER",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS linkedin_followers INTEGER",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS recent_investments JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS recent_news JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS blog_url VARCHAR(2048)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS newsletter_url VARCHAR(2048)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS podcast_url VARCHAR(2048)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS events_attended JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS tier VARCHAR(50)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS category VARCHAR(100)",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS tags JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 5",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS last_scraped_at TIMESTAMP",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS scraped_data JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS scrape_errors JSON",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS internal_notes TEXT",
    "ALTER TABLE gaming_vcs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
]

ALL_MIGRATIONS = OUTLET_COLUMN_MIGRATIONS + STREAMER_COLUMN_MIGRATIONS + VC_COLUMN_MIGRATIONS


def run_migrations(engine) -> None:
    """
    Run all pending column migrations against the live database.
    Safe to call on every startup — all statements use IF NOT EXISTS.
    """
    with engine.connect() as conn:
        for stmt in ALL_MIGRATIONS:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                logger.warning(f"Migration skipped ({e}): {stmt}")
        conn.commit()
    logger.info(f"Column migrations complete ({len(ALL_MIGRATIONS)} statements applied).")
