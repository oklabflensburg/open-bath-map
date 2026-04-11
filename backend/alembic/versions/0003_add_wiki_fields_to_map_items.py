"""Add wiki metadata fields to map_items

Revision ID: 0003_wiki_fields
Revises: 0002_add_postgis_geom
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_wiki_fields"
down_revision = "0002_add_postgis_geom"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("map_items", sa.Column("wikipedia_url", sa.Text(), nullable=True))
    op.add_column("map_items", sa.Column("wikipedia_title", sa.Text(), nullable=True))
    op.add_column("map_items", sa.Column("wikipedia_summary", sa.Text(), nullable=True))
    op.add_column("map_items", sa.Column("wikidata_id", sa.Text(), nullable=True))
    op.add_column("map_items", sa.Column("wikidata_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("map_items", "wikidata_url")
    op.drop_column("map_items", "wikidata_id")
    op.drop_column("map_items", "wikipedia_summary")
    op.drop_column("map_items", "wikipedia_title")
    op.drop_column("map_items", "wikipedia_url")
