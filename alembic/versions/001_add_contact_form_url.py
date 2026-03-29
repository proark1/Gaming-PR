"""Add contact_form_url to gaming_outlets

Revision ID: 001
Revises:
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "gaming_outlets",
        sa.Column("contact_form_url", sa.String(2048), nullable=True),
    )


def downgrade():
    op.drop_column("gaming_outlets", "contact_form_url")
