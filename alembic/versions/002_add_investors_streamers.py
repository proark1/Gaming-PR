"""Add gaming_investors and streamers tables.

Revision ID: 002
Revises: 001
Create Date: 2026-03-29
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gaming_investors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("short_name", sa.String(100), nullable=True),
        sa.Column("investor_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(2048), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("headquarters_city", sa.String(200), nullable=True),
        sa.Column("headquarters_country", sa.String(100), nullable=True),
        sa.Column("headquarters_region", sa.String(10), nullable=True),
        sa.Column("aum_millions", sa.Float(), nullable=True),
        sa.Column("fund_size_millions", sa.Float(), nullable=True),
        sa.Column("typical_check_min_k", sa.Integer(), nullable=True),
        sa.Column("typical_check_max_k", sa.Integer(), nullable=True),
        sa.Column("investment_stages", sa.JSON(), nullable=True),
        sa.Column("focus_areas", sa.JSON(), nullable=True),
        sa.Column("active_regions", sa.JSON(), nullable=True),
        sa.Column("notable_portfolio", sa.JSON(), nullable=True),
        sa.Column("total_known_investments", sa.Integer(), nullable=True),
        sa.Column("contact_name", sa.String(500), nullable=True),
        sa.Column("contact_email", sa.String(500), nullable=True),
        sa.Column("contact_title", sa.String(200), nullable=True),
        sa.Column("linkedin_url", sa.String(2048), nullable=True),
        sa.Column("twitter_url", sa.String(2048), nullable=True),
        sa.Column("crunchbase_url", sa.String(2048), nullable=True),
        sa.Column("pitchbook_url", sa.String(2048), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_gaming_focused", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gaming_investors_id", "gaming_investors", ["id"])
    op.create_index("ix_gaming_investors_name", "gaming_investors", ["name"])
    op.create_index("ix_gaming_investors_is_active", "gaming_investors", ["is_active"])

    op.create_table(
        "streamers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("primary_platform", sa.String(20), nullable=False),
        # Twitch
        sa.Column("twitch_username", sa.String(200), nullable=True),
        sa.Column("twitch_channel_id", sa.String(100), nullable=True),
        sa.Column("twitch_url", sa.String(2048), nullable=True),
        sa.Column("twitch_followers", sa.Integer(), nullable=True),
        sa.Column("twitch_avg_viewers", sa.Integer(), nullable=True),
        sa.Column("twitch_peak_viewers", sa.Integer(), nullable=True),
        sa.Column("twitch_is_partner", sa.Boolean(), nullable=True),
        sa.Column("twitch_is_affiliate", sa.Boolean(), nullable=True),
        sa.Column("twitch_description", sa.Text(), nullable=True),
        sa.Column("twitch_profile_image_url", sa.String(2048), nullable=True),
        sa.Column("twitch_views_total", sa.Integer(), nullable=True),
        # YouTube
        sa.Column("youtube_channel_id", sa.String(100), nullable=True),
        sa.Column("youtube_channel_name", sa.String(500), nullable=True),
        sa.Column("youtube_url", sa.String(2048), nullable=True),
        sa.Column("youtube_subscribers", sa.Integer(), nullable=True),
        sa.Column("youtube_total_views", sa.Integer(), nullable=True),
        sa.Column("youtube_video_count", sa.Integer(), nullable=True),
        sa.Column("youtube_avg_views_per_video", sa.Integer(), nullable=True),
        sa.Column("youtube_description", sa.Text(), nullable=True),
        sa.Column("youtube_profile_image_url", sa.String(2048), nullable=True),
        # X
        sa.Column("x_username", sa.String(200), nullable=True),
        sa.Column("x_user_id", sa.String(100), nullable=True),
        sa.Column("x_url", sa.String(2048), nullable=True),
        sa.Column("x_followers", sa.Integer(), nullable=True),
        sa.Column("x_following", sa.Integer(), nullable=True),
        sa.Column("x_tweet_count", sa.Integer(), nullable=True),
        sa.Column("x_description", sa.Text(), nullable=True),
        sa.Column("x_profile_image_url", sa.String(2048), nullable=True),
        # Other platforms
        sa.Column("instagram_username", sa.String(200), nullable=True),
        sa.Column("instagram_url", sa.String(2048), nullable=True),
        sa.Column("instagram_followers", sa.Integer(), nullable=True),
        sa.Column("tiktok_username", sa.String(200), nullable=True),
        sa.Column("tiktok_url", sa.String(2048), nullable=True),
        sa.Column("tiktok_followers", sa.Integer(), nullable=True),
        # Content
        sa.Column("game_focus", sa.JSON(), nullable=True),
        sa.Column("content_types", sa.JSON(), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("region", sa.String(10), nullable=True),
        # Reach
        sa.Column("total_followers", sa.Integer(), nullable=True),
        sa.Column("estimated_monthly_reach", sa.Integer(), nullable=True),
        # PR
        sa.Column("contact_email", sa.String(500), nullable=True),
        sa.Column("agent_name", sa.String(500), nullable=True),
        sa.Column("agent_email", sa.String(500), nullable=True),
        sa.Column("management_company", sa.String(500), nullable=True),
        sa.Column("media_kit_url", sa.String(2048), nullable=True),
        # Metadata
        sa.Column("profile_image_url", sa.String(2048), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("last_stats_updated_at", sa.DateTime(), nullable=True),
        sa.Column("twitch_last_live_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("twitch_username"),
        sa.UniqueConstraint("youtube_channel_id"),
        sa.UniqueConstraint("x_username"),
    )
    op.create_index("ix_streamers_id", "streamers", ["id"])
    op.create_index("ix_streamers_name", "streamers", ["name"])
    op.create_index("ix_streamers_primary_platform", "streamers", ["primary_platform"])
    op.create_index("ix_streamers_is_active", "streamers", ["is_active"])
    op.create_index("ix_streamers_language", "streamers", ["language"])
    op.create_index("ix_streamers_language_platform", "streamers", ["language", "primary_platform"])
    op.create_index("ix_streamers_total_followers", "streamers", ["total_followers"])


def downgrade() -> None:
    op.drop_table("streamers")
    op.drop_table("gaming_investors")
