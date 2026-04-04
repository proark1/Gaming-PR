"""Add Kick and Rumble platform fields to streamers table.

Revision ID: 003
Revises: 002
Create Date: 2026-04-04
"""
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Kick
    op.add_column("streamers", sa.Column("kick_username", sa.String(200), nullable=True))
    op.add_column("streamers", sa.Column("kick_url", sa.String(2048), nullable=True))
    op.add_column("streamers", sa.Column("kick_followers", sa.Integer(), nullable=True))
    op.add_column("streamers", sa.Column("kick_avg_viewers", sa.Integer(), nullable=True))
    op.add_column("streamers", sa.Column("kick_is_verified", sa.Boolean(), nullable=True))
    op.add_column("streamers", sa.Column("kick_description", sa.Text(), nullable=True))
    op.add_column("streamers", sa.Column("kick_profile_image_url", sa.String(2048), nullable=True))
    op.create_unique_constraint("uq_streamers_kick_username", "streamers", ["kick_username"])

    # Rumble
    op.add_column("streamers", sa.Column("rumble_channel_id", sa.String(200), nullable=True))
    op.add_column("streamers", sa.Column("rumble_url", sa.String(2048), nullable=True))
    op.add_column("streamers", sa.Column("rumble_followers", sa.Integer(), nullable=True))
    op.add_column("streamers", sa.Column("rumble_description", sa.Text(), nullable=True))
    op.add_column("streamers", sa.Column("rumble_profile_image_url", sa.String(2048), nullable=True))
    op.create_unique_constraint("uq_streamers_rumble_channel_id", "streamers", ["rumble_channel_id"])


def downgrade() -> None:
    op.drop_constraint("uq_streamers_rumble_channel_id", "streamers", type_="unique")
    op.drop_column("streamers", "rumble_profile_image_url")
    op.drop_column("streamers", "rumble_description")
    op.drop_column("streamers", "rumble_followers")
    op.drop_column("streamers", "rumble_url")
    op.drop_column("streamers", "rumble_channel_id")

    op.drop_constraint("uq_streamers_kick_username", "streamers", type_="unique")
    op.drop_column("streamers", "kick_profile_image_url")
    op.drop_column("streamers", "kick_description")
    op.drop_column("streamers", "kick_is_verified")
    op.drop_column("streamers", "kick_avg_viewers")
    op.drop_column("streamers", "kick_followers")
    op.drop_column("streamers", "kick_url")
    op.drop_column("streamers", "kick_username")
