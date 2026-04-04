"""Add Phase 3: pitches, deals, coverage, engagement scores, smart follow-ups.

Revision ID: 006
Revises: 005
Create Date: 2026-04-04
"""
import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Generated Pitches ──
    op.create_table(
        "generated_pitches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("target_name", sa.String(500), nullable=False),
        sa.Column("pitch_type", sa.String(30), nullable=False),
        sa.Column("tone", sa.String(20), server_default="professional"),
        sa.Column("user_instructions", sa.Text(), nullable=True),
        sa.Column("company_snapshot", sa.JSON(), nullable=True),
        sa.Column("contact_snapshot", sa.JSON(), nullable=True),
        sa.Column("subject_line", sa.String(1000), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("claude_model_used", sa.String(50), nullable=True),
        sa.Column("generation_tokens", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), server_default="generating"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("sent_via_campaign_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["company_profiles.id"]),
        sa.ForeignKeyConstraint(["sent_via_campaign_id"], ["campaigns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_pitches_id", "generated_pitches", ["id"])
    op.create_index("ix_generated_pitches_company_id", "generated_pitches", ["company_id"])

    # ── Deals ──
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("contact_type", sa.String(20), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("contact_name", sa.String(500), nullable=False),
        sa.Column("deal_type", sa.String(30), nullable=False),
        sa.Column("stage", sa.String(30), nullable=False, server_default="interested"),
        sa.Column("stage_changed_at", sa.DateTime(), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deal_value_usd", sa.Float(), nullable=True),
        sa.Column("payment_terms", sa.String(30), nullable=True),
        sa.Column("contract_url", sa.String(2048), nullable=True),
        sa.Column("pitch_deck_url", sa.String(2048), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        sa.Column("actual_close_date", sa.Date(), nullable=True),
        sa.Column("source_campaign_id", sa.Integer(), nullable=True),
        sa.Column("source_pitch_id", sa.Integer(), nullable=True),
        sa.Column("deliverables", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["company_profiles.id"]),
        sa.ForeignKeyConstraint(["source_campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["source_pitch_id"], ["generated_pitches.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deals_id", "deals", ["id"])
    op.create_index("ix_deals_company_id", "deals", ["company_id"])
    op.create_index("ix_deal_company_stage", "deals", ["company_id", "stage"])
    op.create_index("ix_deal_contact", "deals", ["contact_type", "contact_id"])

    # ── Deal Stage History ──
    op.create_table(
        "deal_stage_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deal_id", sa.Integer(), nullable=False),
        sa.Column("from_stage", sa.String(30), nullable=False),
        sa.Column("to_stage", sa.String(30), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deal_stage_history_id", "deal_stage_history", ["id"])
    op.create_index("ix_deal_stage_history_deal_id", "deal_stage_history", ["deal_id"])

    # ── Press Coverage ──
    op.create_table(
        "press_coverage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("outlet_id", sa.Integer(), nullable=True),
        sa.Column("outlet_name", sa.String(500), nullable=False),
        sa.Column("article_url", sa.String(2048), nullable=False, unique=True),
        sa.Column("article_title", sa.String(1000), nullable=False),
        sa.Column("scraped_article_id", sa.Integer(), nullable=True),
        sa.Column("source_campaign_id", sa.Integer(), nullable=True),
        sa.Column("coverage_type", sa.String(30), server_default="news_mention"),
        sa.Column("sentiment", sa.String(20), server_default="neutral"),
        sa.Column("prominence", sa.String(20), server_default="mentioned"),
        sa.Column("estimated_reach", sa.Integer(), nullable=True),
        sa.Column("estimated_media_value_usd", sa.Float(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("rating_score", sa.Float(), nullable=True),
        sa.Column("rating_max", sa.Float(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("discovered_at", sa.DateTime(), nullable=True),
        sa.Column("verified", sa.Boolean(), server_default="FALSE"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["company_profiles.id"]),
        sa.ForeignKeyConstraint(["outlet_id"], ["gaming_outlets.id"]),
        sa.ForeignKeyConstraint(["scraped_article_id"], ["scraped_articles.id"]),
        sa.ForeignKeyConstraint(["source_campaign_id"], ["campaigns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_press_coverage_id", "press_coverage", ["id"])
    op.create_index("ix_press_coverage_company_id", "press_coverage", ["company_id"])
    op.create_index("ix_coverage_company", "press_coverage", ["company_id", "published_at"])

    # ── Contact Engagement Scores ──
    op.create_table(
        "contact_engagement_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("contact_type", sa.String(20), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("total_emails_received", sa.Integer(), server_default="0"),
        sa.Column("total_opens", sa.Integer(), server_default="0"),
        sa.Column("total_clicks", sa.Integer(), server_default="0"),
        sa.Column("total_replies", sa.Integer(), server_default="0"),
        sa.Column("open_rate", sa.Float(), server_default="0"),
        sa.Column("click_rate", sa.Float(), server_default="0"),
        sa.Column("reply_rate", sa.Float(), server_default="0"),
        sa.Column("avg_response_time_hours", sa.Float(), nullable=True),
        sa.Column("engagement_score", sa.Float(), server_default="50"),
        sa.Column("last_computed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contact_type", "contact_id", name="uq_engagement_contact"),
    )
    op.create_index("ix_contact_engagement_scores_id", "contact_engagement_scores", ["id"])
    op.create_index("ix_engagement_score", "contact_engagement_scores", ["contact_type", "engagement_score"])

    # ── Smart follow-up columns on campaigns ──
    for col, coltype in [
        ("smart_follow_up_enabled", "BOOLEAN DEFAULT FALSE"),
        ("follow_up_opened_no_reply_message_id", "INTEGER"),
        ("follow_up_clicked_no_reply_message_id", "INTEGER"),
        ("follow_up_never_opened_message_id", "INTEGER"),
    ]:
        try:
            op.add_column("campaigns", sa.Column(col,
                sa.Boolean() if "BOOLEAN" in coltype else sa.Integer()))
        except Exception:
            pass

    # ── follow_up_trigger on outreach_records ──
    try:
        op.add_column("outreach_records", sa.Column("follow_up_trigger", sa.String(30)))
    except Exception:
        pass


def downgrade() -> None:
    op.drop_table("contact_engagement_scores")
    op.drop_table("press_coverage")
    op.drop_table("deal_stage_history")
    op.drop_table("deals")
    op.drop_table("generated_pitches")

    for col in ["smart_follow_up_enabled", "follow_up_opened_no_reply_message_id",
                "follow_up_clicked_no_reply_message_id", "follow_up_never_opened_message_id"]:
        try:
            op.drop_column("campaigns", col)
        except Exception:
            pass
    try:
        op.drop_column("outreach_records", "follow_up_trigger")
    except Exception:
        pass
