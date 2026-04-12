"""Add bathing_profile_url to map_items

Revision ID: 0004_bathing_profile_url
Revises: 0003_wiki_fields
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_bathing_profile_url"
down_revision = "0003_wiki_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE map_items ADD COLUMN IF NOT EXISTS bathing_profile_url TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE map_items DROP COLUMN IF EXISTS bathing_profile_url")
