"""Add company_profiles, streamer_snapshots, contact_activities tables and scoring/CRM columns.

Revision ID: 005
Revises: 004
Create Date: 2026-04-04
"""
import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Company Profiles ──
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(2048), nullable=True),
        sa.Column("logo_url", sa.String(2048), nullable=True),
        sa.Column("genre", sa.JSON(), nullable=True),
        sa.Column("platforms", sa.JSON(), nullable=True),
        sa.Column("release_stage", sa.String(30), nullable=True),
        sa.Column("target_audience", sa.JSON(), nullable=True),
        sa.Column("funding_stage", sa.String(30), nullable=True),
        sa.Column("funding_target_k", sa.Integer(), nullable=True),
        sa.Column("marketing_budget_k", sa.Integer(), nullable=True),
        sa.Column("team_size", sa.Integer(), nullable=True),
        sa.Column("revenue_model", sa.String(50), nullable=True),
        sa.Column("preferred_streamer_tiers", sa.JSON(), nullable=True),
        sa.Column("preferred_regions", sa.JSON(), nullable=True),
        sa.Column("preferred_platforms", sa.JSON(), nullable=True),
        sa.Column("preferred_investor_types", sa.JSON(), nullable=True),
        sa.Column("trailer_url", sa.String(2048), nullable=True),
        sa.Column("pitch_deck_url", sa.String(2048), nullable=True),
        sa.Column("media_kit_url", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_profiles_id", "company_profiles", ["id"])
    op.create_index("ix_company_profiles_user_id", "company_profiles", ["user_id"])

    # ── Streamer Snapshots ──
    op.create_table(
        "streamer_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("streamer_id", sa.Integer(), nullable=False),
        sa.Column("total_followers", sa.BigInteger(), nullable=True),
        sa.Column("twitch_followers", sa.Integer(), nullable=True),
        sa.Column("youtube_subscribers", sa.Integer(), nullable=True),
        sa.Column("kick_followers", sa.Integer(), nullable=True),
        sa.Column("twitch_avg_viewers", sa.Integer(), nullable=True),
        sa.Column("engagement_rate", sa.Float(), nullable=True),
        sa.Column("influence_score", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["streamer_id"], ["streamers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_streamer_snapshots_id", "streamer_snapshots", ["id"])
    op.create_index("ix_streamer_snapshots_streamer_id", "streamer_snapshots", ["streamer_id"])
    op.create_index("ix_streamer_snapshots_captured_at", "streamer_snapshots", ["captured_at"])
    op.create_index("ix_snapshot_streamer_date", "streamer_snapshots", ["streamer_id", "captured_at"])

    # ── Contact Activities ──
    op.create_table(
        "contact_activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_type", sa.String(20), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("activity_type", sa.String(50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contact_activities_id", "contact_activities", ["id"])
    op.create_index("ix_activity_contact", "contact_activities", ["contact_type", "contact_id"])
    op.create_index("ix_activity_created", "contact_activities", ["created_at"])

    # ── Scoring columns on streamers ──
    for col, coltype in [
        ("engagement_rate", "FLOAT"),
        ("platform_count", "INTEGER"),
        ("influence_score", "FLOAT"),
        ("influence_tier", "VARCHAR(20)"),
        ("estimated_cpm_usd", "FLOAT"),
        ("sponsorship_rate_usd", "FLOAT"),
    ]:
        try:
            op.add_column("streamers", sa.Column(col, sa.Text() if "VARCHAR" in coltype else sa.Float() if coltype == "FLOAT" else sa.Integer()))
        except Exception:
            pass

    # ── CRM columns on streamers (if not already present from auto-migrate) ──
    for col, coltype in [
        ("relationship_stage", "VARCHAR(30)"),
        ("last_contacted_at", "DATETIME"),
        ("last_responded_at", "DATETIME"),
        ("total_outreach_count", "INTEGER"),
    ]:
        try:
            if coltype == "DATETIME":
                op.add_column("streamers", sa.Column(col, sa.DateTime()))
            elif coltype == "INTEGER":
                op.add_column("streamers", sa.Column(col, sa.Integer(), server_default="0"))
            else:
                op.add_column("streamers", sa.Column(col, sa.String(30)))
        except Exception:
            pass

    # ── CRM columns on gaming_outlets (if not already present) ──
    for col, coltype in [
        ("relationship_stage", "VARCHAR(30)"),
        ("last_contacted_at", "DATETIME"),
        ("last_responded_at", "DATETIME"),
        ("total_outreach_count", "INTEGER"),
    ]:
        try:
            if coltype == "DATETIME":
                op.add_column("gaming_outlets", sa.Column(col, sa.DateTime()))
            elif coltype == "INTEGER":
                op.add_column("gaming_outlets", sa.Column(col, sa.Integer(), server_default="0"))
            else:
                op.add_column("gaming_outlets", sa.Column(col, sa.String(30)))
        except Exception:
            pass

    # ── CRM columns on gaming_investors (if not already present) ──
    for col, coltype in [
        ("relationship_stage", "VARCHAR(30)"),
        ("last_contacted_at", "DATETIME"),
        ("last_responded_at", "DATETIME"),
        ("total_outreach_count", "INTEGER"),
    ]:
        try:
            if coltype == "DATETIME":
                op.add_column("gaming_investors", sa.Column(col, sa.DateTime()))
            elif coltype == "INTEGER":
                op.add_column("gaming_investors", sa.Column(col, sa.Integer(), server_default="0"))
            else:
                op.add_column("gaming_investors", sa.Column(col, sa.String(30)))
        except Exception:
            pass


def downgrade() -> None:
    op.drop_table("contact_activities")
    op.drop_table("streamer_snapshots")
    op.drop_table("company_profiles")

    for col in ["engagement_rate", "platform_count", "influence_score",
                "influence_tier", "estimated_cpm_usd", "sponsorship_rate_usd",
                "relationship_stage", "last_contacted_at", "last_responded_at",
                "total_outreach_count"]:
        try:
            op.drop_column("streamers", col)
        except Exception:
            pass

    for col in ["relationship_stage", "last_contacted_at", "last_responded_at", "total_outreach_count"]:
        try:
            op.drop_column("gaming_outlets", col)
        except Exception:
            pass
        try:
            op.drop_column("gaming_investors", col)
        except Exception:
            pass
