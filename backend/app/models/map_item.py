from datetime import datetime
from datetime import date
from typing import Literal

from pydantic import Field

from app.models.bathing_site import ApiModel

MapItemType = Literal["badestelle", "poi"]


class MapPointGeometry(ApiModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class MapItem(ApiModel):
    id: str
    slug: str
    type: MapItemType
    title: str
    description: str | None = None
    category: str | None = None
    lat: float
    lng: float
    address: str | None = None
    postcode: str | None = None
    city: str | None = None
    image_url: str | None = None
    website: str | None = None
    tags: list[str] = Field(default_factory=list)
    water_quality: str | None = None
    accessibility: str | None = None
    possible_pollutions: str | None = None
    seasonal_status: str | None = None
    season_start: date | None = None
    season_end: date | None = None
    last_update: datetime | None = None
    district: str | None = None
    opening_hours: str | None = None
    amenities: list[str] = Field(default_factory=list)
    distance_km: float | None = None


class MapFeatureProperties(ApiModel):
    id: str
    slug: str
    type: MapItemType
    title: str
    category: str | None = None
    city: str | None = None
    water_quality: str | None = None


class MapFeature(ApiModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: MapPointGeometry
    properties: MapFeatureProperties


class MapFilters(ApiModel):
    types: list[MapItemType] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    infrastructures: list[str] = Field(default_factory=list)


class MapFeatureCollection(ApiModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[MapFeature] = Field(default_factory=list)
    filters: MapFilters = Field(default_factory=MapFilters)
    total: int = 0
