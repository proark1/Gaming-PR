"""Add performance indices for content_hash, article_type, and is_full_content.

These columns are queried on every scrape stats request, monitoring dashboard,
and SimHash dedup pre-load, but previously had no index — causing full table scans.

Revision ID: 001
Revises:
Create Date: 2026-03-29
"""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_scraped_articles_content_hash",
        "scraped_articles",
        ["content_hash"],
    )
    op.create_index(
        "ix_scraped_articles_article_type",
        "scraped_articles",
        ["article_type"],
    )
    op.create_index(
        "ix_scraped_articles_is_full_content",
        "scraped_articles",
        ["is_full_content"],
    )


def downgrade() -> None:
    op.drop_index("ix_scraped_articles_content_hash", table_name="scraped_articles")
    op.drop_index("ix_scraped_articles_article_type", table_name="scraped_articles")
    op.drop_index("ix_scraped_articles_is_full_content", table_name="scraped_articles")
