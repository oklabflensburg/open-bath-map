from __future__ import annotations

from datetime import date, datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, Integer, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlmodel import Field, SQLModel


class DatasetStateRecord(SQLModel, table=True):
    __tablename__ = "dataset_state"

    id: int = Field(default=1, sa_column=Column(SmallInteger, primary_key=True))
    data_updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    synced_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    source_urls: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))


class BathingSiteRecord(SQLModel, table=True):
    __tablename__ = "bathing_sites"

    id: str = Field(primary_key=True)
    name: str
    short_name: str | None = None
    common_name: str | None = None
    municipality: str | None = None
    district: str | None = None
    region: str | None = None
    water_category: str | None = None
    coastal_water: str | None = None
    bathing_water_type: str | None = None
    bathing_spot_length_m: float | None = Field(default=None, sa_column=Column(Float))
    description: str | None = None
    bathing_spot_information: str | None = None
    impacts_on_bathing_water: str | None = None
    possible_pollutions: str | None = None
    infrastructure: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(Text), nullable=False))
    water_quality: str | None = None
    water_quality_from_year: int | None = Field(default=None, sa_column=Column(Integer))
    water_quality_to_year: int | None = Field(default=None, sa_column=Column(Integer))
    seasonal_status: str | None = None
    season_start: date | None = None
    season_end: date | None = None
    last_sample_date: date | None = None
    sample_type: str | None = None
    intestinal_enterococci: float | None = Field(default=None, sa_column=Column(Float))
    e_coli: float | None = Field(default=None, sa_column=Column(Float))
    water_temperature_c: float | None = Field(default=None, sa_column=Column(Float))
    air_temperature_c: float | None = Field(default=None, sa_column=Column(Float))
    transparency_m: float | None = Field(default=None, sa_column=Column(Float))
    source_url: str
    source_dataset: str
    search_text: str
    lat: float = Field(sa_column=Column(Float, nullable=False))
    lon: float = Field(sa_column=Column(Float, nullable=False))
    geom: Any = Field(sa_column=Column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False))


class MapItemRecord(SQLModel, table=True):
    __tablename__ = "map_items"
    __table_args__ = (UniqueConstraint("slug", name="uq_map_items_slug"),)

    id: str = Field(primary_key=True)
    slug: str
    type: str
    title: str
    description: str | None = None
    category: str | None = None
    lat: float = Field(sa_column=Column(Float, nullable=False))
    lng: float = Field(sa_column=Column(Float, nullable=False))
    address: str | None = None
    postcode: str | None = None
    city: str | None = None
    municipality: str | None = None
    image_url: str | None = None
    bathing_profile_url: str | None = None
    website: str | None = None
    wikipedia_url: str | None = None
    wikipedia_title: str | None = None
    wikipedia_summary: str | None = None
    wikidata_id: str | None = None
    wikidata_url: str | None = None
    source_name: str | None = None
    content_license: str | None = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(Text), nullable=False))
    water_quality: str | None = None
    accessibility: str | None = None
    possible_pollutions: str | None = None
    seasonal_status: str | None = None
    season_start: date | None = None
    season_end: date | None = None
    sample_type: str | None = None
    intestinal_enterococci: float | None = Field(default=None, sa_column=Column(Float))
    e_coli: float | None = Field(default=None, sa_column=Column(Float))
    water_temperature_c: float | None = Field(default=None, sa_column=Column(Float))
    air_temperature_c: float | None = Field(default=None, sa_column=Column(Float))
    transparency_m: float | None = Field(default=None, sa_column=Column(Float))
    last_update: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    district: str | None = None
    opening_hours: str | None = None
    amenities: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(Text), nullable=False))
    search_text: str
    geom: Any = Field(sa_column=Column(Geometry("POINT", srid=4326, spatial_index=True), nullable=False))
