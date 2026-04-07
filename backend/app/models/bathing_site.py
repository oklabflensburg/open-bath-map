from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class SiteCoordinates(ApiModel):
    lat: float
    lon: float


class BathingSite(ApiModel):
    id: str
    name: str
    short_name: str | None = None
    common_name: str | None = None
    municipality: str | None = None
    district: str | None = None
    region: str | None = None
    water_category: str | None = None
    coastal_water: str | None = None
    bathing_water_type: str | None = None
    bathing_spot_length_m: float | None = None
    description: str | None = None
    bathing_spot_information: str | None = None
    impacts_on_bathing_water: str | None = None
    possible_pollutions: str | None = None
    infrastructure: list[str] = Field(default_factory=list)
    water_quality: str | None = None
    water_quality_from_year: int | None = None
    water_quality_to_year: int | None = None
    seasonal_status: str | None = None
    season_start: date | None = None
    season_end: date | None = None
    last_sample_date: date | None = None
    source_url: str
    source_dataset: str
    coordinates: SiteCoordinates
    distance_km: float | None = None


class FilterOptions(ApiModel):
    districts: list[str] = Field(default_factory=list)
    municipalities: list[str] = Field(default_factory=list)
    water_categories: list[str] = Field(default_factory=list)
    coastal_waters: list[str] = Field(default_factory=list)
    bathing_water_types: list[str] = Field(default_factory=list)
    water_qualities: list[str] = Field(default_factory=list)
    infrastructures: list[str] = Field(default_factory=list)


class BathingSiteListResponse(ApiModel):
    items: list[BathingSite]
    total: int
    filter_options: FilterOptions
    data_updated_at: datetime


class HealthResponse(ApiModel):
    status: str
    cache_age_seconds: int | None = None
    cached_at: datetime | None = None
    source_urls: dict[str, str]
    item_count: int
