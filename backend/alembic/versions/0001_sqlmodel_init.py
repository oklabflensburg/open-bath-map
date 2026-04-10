"""Initial SQLModel schema

Revision ID: 0001_sqlmodel_init
Revises:
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql


revision = "0001_sqlmodel_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION immutable_unaccent(TEXT)
        RETURNS TEXT
        LANGUAGE sql
        IMMUTABLE
        PARALLEL SAFE
        AS $$
            SELECT public.unaccent($1)
        $$;
        """
    )

    op.create_table(
        "dataset_state",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("data_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_urls", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )

    op.create_table(
        "bathing_sites",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("short_name", sa.Text()),
        sa.Column("common_name", sa.Text()),
        sa.Column("municipality", sa.Text()),
        sa.Column("district", sa.Text()),
        sa.Column("region", sa.Text()),
        sa.Column("water_category", sa.Text()),
        sa.Column("coastal_water", sa.Text()),
        sa.Column("bathing_water_type", sa.Text()),
        sa.Column("bathing_spot_length_m", sa.Float()),
        sa.Column("description", sa.Text()),
        sa.Column("bathing_spot_information", sa.Text()),
        sa.Column("impacts_on_bathing_water", sa.Text()),
        sa.Column("possible_pollutions", sa.Text()),
        sa.Column("infrastructure", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("water_quality", sa.Text()),
        sa.Column("water_quality_from_year", sa.Integer()),
        sa.Column("water_quality_to_year", sa.Integer()),
        sa.Column("seasonal_status", sa.Text()),
        sa.Column("season_start", sa.Date()),
        sa.Column("season_end", sa.Date()),
        sa.Column("last_sample_date", sa.Date()),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_dataset", sa.Text(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("geom", Geometry("POINT", srid=4326), nullable=False),
    )
    op.create_index("idx_bathing_sites_coords", "bathing_sites", ["lat", "lon"])
    op.execute("CREATE INDEX IF NOT EXISTS idx_bathing_sites_geom ON bathing_sites USING GIST (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bathing_sites_search_german ON bathing_sites USING GIN (to_tsvector('german', search_text))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bathing_sites_search_trgm ON bathing_sites USING GIN (immutable_unaccent(lower(search_text)) gin_trgm_ops)")

    op.create_table(
        "map_items",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.Text()),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("postcode", sa.Text()),
        sa.Column("city", sa.Text()),
        sa.Column("municipality", sa.Text()),
        sa.Column("image_url", sa.Text()),
        sa.Column("website", sa.Text()),
        sa.Column("source_name", sa.Text()),
        sa.Column("content_license", sa.Text()),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("water_quality", sa.Text()),
        sa.Column("accessibility", sa.Text()),
        sa.Column("possible_pollutions", sa.Text()),
        sa.Column("seasonal_status", sa.Text()),
        sa.Column("season_start", sa.Date()),
        sa.Column("season_end", sa.Date()),
        sa.Column("last_update", sa.DateTime(timezone=True)),
        sa.Column("district", sa.Text()),
        sa.Column("opening_hours", sa.Text()),
        sa.Column("amenities", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("geom", Geometry("POINT", srid=4326), nullable=False),
        sa.UniqueConstraint("slug", name="uq_map_items_slug"),
    )
    op.create_index("idx_map_items_coords", "map_items", ["lat", "lng"])
    op.execute("CREATE INDEX IF NOT EXISTS idx_map_items_geom ON map_items USING GIST (geom)")
    op.create_index("idx_map_items_type_category", "map_items", ["type", "category"])
    op.execute("CREATE INDEX IF NOT EXISTS idx_map_items_search_german ON map_items USING GIN (to_tsvector('german', search_text))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_map_items_search_trgm ON map_items USING GIN (immutable_unaccent(lower(search_text)) gin_trgm_ops)")


def downgrade() -> None:
    op.drop_index("idx_map_items_type_category", table_name="map_items")
    op.drop_index("idx_map_items_coords", table_name="map_items")
    op.execute("DROP INDEX IF EXISTS idx_map_items_geom")
    op.execute("DROP INDEX IF EXISTS idx_map_items_search_trgm")
    op.execute("DROP INDEX IF EXISTS idx_map_items_search_german")
    op.drop_table("map_items")

    op.drop_index("idx_bathing_sites_coords", table_name="bathing_sites")
    op.execute("DROP INDEX IF EXISTS idx_bathing_sites_geom")
    op.execute("DROP INDEX IF EXISTS idx_bathing_sites_search_trgm")
    op.execute("DROP INDEX IF EXISTS idx_bathing_sites_search_german")
    op.drop_table("bathing_sites")

    op.drop_table("dataset_state")
    op.execute("DROP FUNCTION IF EXISTS immutable_unaccent(TEXT)")
