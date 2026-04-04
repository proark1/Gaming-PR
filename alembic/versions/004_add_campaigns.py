"""Add campaigns, outreach_records, and do_not_contact tables.

Revision ID: 004
Revises: 003
Create Date: 2026-04-04
"""
import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("domain_id", sa.Integer(), nullable=True),
        sa.Column("from_email", sa.String(255), nullable=True),
        sa.Column("from_name", sa.String(255), nullable=True),
        sa.Column("reply_to", sa.String(255), nullable=True),
        sa.Column("target_types", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("target_filters", sa.JSON(), nullable=True),
        sa.Column("target_ids_override", sa.JSON(), nullable=True),
        sa.Column("send_start_at", sa.DateTime(), nullable=True),
        sa.Column("send_window_start", sa.String(5), nullable=True),
        sa.Column("send_window_end", sa.String(5), nullable=True),
        sa.Column("send_window_timezone", sa.String(50), server_default="UTC"),
        sa.Column("batch_size", sa.Integer(), server_default="20"),
        sa.Column("batch_delay_seconds", sa.Integer(), server_default="300"),
        sa.Column("follow_up_enabled", sa.Boolean(), server_default="0"),
        sa.Column("follow_up_delay_days", sa.Integer(), server_default="3"),
        sa.Column("follow_up_message_id", sa.Integer(), nullable=True),
        sa.Column("max_follow_ups", sa.Integer(), server_default="1"),
        sa.Column("total_targets", sa.Integer(), server_default="0"),
        sa.Column("personalized_count", sa.Integer(), server_default="0"),
        sa.Column("sent_count", sa.Integer(), server_default="0"),
        sa.Column("delivered_count", sa.Integer(), server_default="0"),
        sa.Column("opened_count", sa.Integer(), server_default="0"),
        sa.Column("clicked_count", sa.Integer(), server_default="0"),
        sa.Column("bounced_count", sa.Integer(), server_default="0"),
        sa.Column("replied_count", sa.Integer(), server_default="0"),
        sa.Column("failed_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("launched_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["domain_id"], ["connected_domains.id"]),
        sa.ForeignKeyConstraint(["follow_up_message_id"], ["messages.id"]),
    )
    op.create_index("ix_campaigns_id", "campaigns", ["id"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])

    op.create_table(
        "outreach_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("personalization_id", sa.Integer(), nullable=True),
        sa.Column("sent_email_id", sa.Integer(), nullable=True),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("target_name", sa.String(500), nullable=False),
        sa.Column("target_email", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("skip_reason", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("follow_up_number", sa.Integer(), server_default="0"),
        sa.Column("parent_outreach_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_send_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=True),
        sa.Column("clicked_at", sa.DateTime(), nullable=True),
        sa.Column("replied_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["personalization_id"], ["message_personalizations.id"]),
        sa.ForeignKeyConstraint(["sent_email_id"], ["sent_emails.id"]),
        sa.ForeignKeyConstraint(["parent_outreach_id"], ["outreach_records.id"]),
        sa.UniqueConstraint(
            "campaign_id", "target_type", "target_id", "follow_up_number",
            name="uq_outreach_target",
        ),
    )
    op.create_index("ix_outreach_records_id", "outreach_records", ["id"])
    op.create_index("ix_outreach_records_campaign_id", "outreach_records", ["campaign_id"])
    op.create_index(
        "ix_outreach_records_campaign_status",
        "outreach_records",
        ["campaign_id", "status"],
    )

    op.create_table(
        "do_not_contact",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(500), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_dnc_email"),
    )
    op.create_index("ix_do_not_contact_id", "do_not_contact", ["id"])
    op.create_index("ix_do_not_contact_email", "do_not_contact", ["email"])


def downgrade() -> None:
    op.drop_table("do_not_contact")
    op.drop_table("outreach_records")
    op.drop_table("campaigns")
