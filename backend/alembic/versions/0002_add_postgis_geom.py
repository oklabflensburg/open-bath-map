"""Add PostGIS geometry columns

Revision ID: 0002_add_postgis_geom
Revises: 0001_sqlmodel_init
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


revision = "0002_add_postgis_geom"
down_revision = "0001_sqlmodel_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.add_column("bathing_sites", sa.Column("geom", Geometry("POINT", srid=4326), nullable=True))
    op.add_column("map_items", sa.Column("geom", Geometry("POINT", srid=4326), nullable=True))
    op.execute("UPDATE bathing_sites SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326) WHERE geom IS NULL")
    op.execute("UPDATE map_items SET geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326) WHERE geom IS NULL")
    op.alter_column("bathing_sites", "geom", nullable=False)
    op.alter_column("map_items", "geom", nullable=False)
    op.execute("CREATE INDEX IF NOT EXISTS idx_bathing_sites_geom ON bathing_sites USING GIST (geom)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_map_items_geom ON map_items USING GIST (geom)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_map_items_geom")
    op.execute("DROP INDEX IF EXISTS idx_bathing_sites_geom")
    op.drop_column("map_items", "geom")
    op.drop_column("bathing_sites", "geom")
