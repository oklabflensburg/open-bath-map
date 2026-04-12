"""Add latest measurement fields to bathing_sites and map_items

Revision ID: 0005_measurements
Revises: 0004_bathing_profile_url
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_measurements"
down_revision = "0004_bathing_profile_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE bathing_sites ADD COLUMN IF NOT EXISTS sample_type TEXT")
    op.execute("ALTER TABLE bathing_sites ADD COLUMN IF NOT EXISTS intestinal_enterococci DOUBLE PRECISION")
    op.execute("ALTER TABLE bathing_sites ADD COLUMN IF NOT EXISTS e_coli DOUBLE PRECISION")
    op.execute("ALTER TABLE bathing_sites ADD COLUMN IF NOT EXISTS water_temperature_c DOUBLE PRECISION")
    op.execute("ALTER TABLE bathing_sites ADD COLUMN IF NOT EXISTS air_temperature_c DOUBLE PRECISION")
    op.execute("ALTER TABLE bathing_sites ADD COLUMN IF NOT EXISTS transparency_m DOUBLE PRECISION")

    op.execute("ALTER TABLE map_items ADD COLUMN IF NOT EXISTS sample_type TEXT")
    op.execute("ALTER TABLE map_items ADD COLUMN IF NOT EXISTS intestinal_enterococci DOUBLE PRECISION")
    op.execute("ALTER TABLE map_items ADD COLUMN IF NOT EXISTS e_coli DOUBLE PRECISION")
    op.execute("ALTER TABLE map_items ADD COLUMN IF NOT EXISTS water_temperature_c DOUBLE PRECISION")
    op.execute("ALTER TABLE map_items ADD COLUMN IF NOT EXISTS air_temperature_c DOUBLE PRECISION")
    op.execute("ALTER TABLE map_items ADD COLUMN IF NOT EXISTS transparency_m DOUBLE PRECISION")


def downgrade() -> None:
    op.execute("ALTER TABLE map_items DROP COLUMN IF EXISTS transparency_m")
    op.execute("ALTER TABLE map_items DROP COLUMN IF EXISTS air_temperature_c")
    op.execute("ALTER TABLE map_items DROP COLUMN IF EXISTS water_temperature_c")
    op.execute("ALTER TABLE map_items DROP COLUMN IF EXISTS e_coli")
    op.execute("ALTER TABLE map_items DROP COLUMN IF EXISTS intestinal_enterococci")
    op.execute("ALTER TABLE map_items DROP COLUMN IF EXISTS sample_type")

    op.execute("ALTER TABLE bathing_sites DROP COLUMN IF EXISTS transparency_m")
    op.execute("ALTER TABLE bathing_sites DROP COLUMN IF EXISTS air_temperature_c")
    op.execute("ALTER TABLE bathing_sites DROP COLUMN IF EXISTS water_temperature_c")
    op.execute("ALTER TABLE bathing_sites DROP COLUMN IF EXISTS e_coli")
    op.execute("ALTER TABLE bathing_sites DROP COLUMN IF EXISTS intestinal_enterococci")
    op.execute("ALTER TABLE bathing_sites DROP COLUMN IF EXISTS sample_type")
