from __future__ import annotations

import csv
import io
import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.models.bathing_site import BathingSite, BathingSiteListResponse, FilterOptions, SiteCoordinates
from app.models.map_item import MapFeature, MapFeatureCollection, MapFeatureProperties, MapFilters, MapItem, MapItemType, MapPointGeometry

CKAN_API_URL = "https://opendata.schleswig-holstein.de/api/3/action/package_search"

SOURCE_QUERIES = {
    "stammdaten": {
        "term": "badegewasser stammdaten",
        "title": "Badegewässer Stammdaten",
        "preferred_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_badegewaesser_odata.csv",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_badegewaesser_odata.csv",
    },
    "einstufung": {
        "term": "badegewasser einstufung",
        "title": "Badegewässer Einstufung",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_einstufung_odata.csv",
    },
    "infrastruktur": {
        "term": "badegewasser infrastruktur",
        "title": "Badegewässer Infrastruktur",
        "preferred_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_infrastruktur_odata.csv",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_infrastruktur_odata.csv",
    },
    "saison": {
        "term": "badegewasser saisondauer",
        "title": "Badegewässer Saisondauer",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_badesaison_odata.csv",
    },
    "messungen": {
        "term": "badegewasser messungen",
        "title": "Badegewässer Messungen",
        "preferred_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_proben_odata.csv",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_proben_odata.csv",
    },
}

STAMMDATEN_COLUMNS = [
    "bathing_water_id",
    "bathing_water_name",
    "short_name",
    "common_name",
    "water_category",
    "coastal_water",
    "bathing_water_type",
    "description",
    "bathing_spot_length_m",
    "eu_registration",
    "eu_deregistration",
    "river_basin_district_id",
    "river_basin_district_name",
    "water_body_id",
    "water_body_name",
    "natural_water_body_id",
    "natural_water_body_name",
    "keywords",
    "district_number",
    "district",
    "municipality_number",
    "municipality",
    "utm_east",
    "utm_north",
    "lon",
    "lat",
    "bathing_spot_information",
    "impacts_on_bathing_water",
    "possible_pollutions",
]

EINSTUFUNG_COLUMNS = ["bathing_water_id", "from_year", "to_year", "water_quality"]
INFRASTRUCTURE_COLUMNS = ["bathing_water_id", "infrastructure_id", "infrastructure_label"]
SAISON_COLUMNS = ["bathing_water_id", "season_start", "season_end", "seasonal_status"]
MEASUREMENT_COLUMNS = [
    "bathing_water_id",
    "bathing_water_name",
    "sampling_point",
    "water_depth_cm",
    "monitoring_reason",
    "water_category",
    "coastal_water",
    "measurement_id",
    "sample_date",
    "sample_type",
    "intestinal_enterococci",
    "e_coli",
    "water_temperature_c",
    "air_temperature_c",
    "transparency_m",
]


@dataclass
class CachedDataset:
    items: list[BathingSite]
    data_updated_at: datetime
    source_urls: dict[str, str]
    cached_at: datetime


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        parsed_date = _parse_date(value)
        if parsed_date is None:
            return None
        return datetime.combine(parsed_date, datetime.min.time())


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\r", " ").replace("\xa0", " ")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = text.strip(" ,;\n")
    return text or None


def _as_sorted_values(values: list[str | None]) -> list[str]:
    cleaned = sorted({value for value in values if value})
    return cleaned


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold())
    return slug.strip("-")


def _title_case_preserving_separators(value: str) -> str:
    return re.sub(
        r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'/-]*",
        lambda match: match.group(0).capitalize(),
        value.casefold(),
    )


def _normalize_bathing_title(value: str) -> str:
    normalized = _title_case_preserving_separators(value)
    normalized = normalized.replace("St. Peter-ording", "St. Peterording")
    return normalized


def _split_bathing_name_parts(value: str | None) -> list[str]:
    cleaned = _clean_text(value)
    if not cleaned:
        return []
    return [part.strip() for part in cleaned.split(";") if part.strip()]


def _normalize_bathing_region(value: str | None) -> str | None:
    if not value:
        return None
    mapping = {
        "nords": "Nordsee",
        "osts": "Ostsee",
    }
    return mapping.get(value.casefold())


def _canonical_slug_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    normalized = value.casefold()
    normalized = normalized.replace("st.", "sankt")
    normalized = normalized.replace("st ", "sankt ")
    normalized = normalized.replace("peter-ording", "peter ording")
    normalized = normalized.replace("peterording", "peter ording")
    slug = _slugify(normalized)
    return {part for part in slug.split("-") if part}


def _is_redundant_slug_part(base: str, candidate: str) -> bool:
    candidate_tokens = _canonical_slug_tokens(candidate)
    if not candidate_tokens:
        return True
    base_tokens = _canonical_slug_tokens(base)
    return candidate_tokens.issubset(base_tokens)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class OpenDataService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.cache_path = Path(self.settings.cache_dir) / "bathing-sites-cache.json"
        self.poi_path = Path(__file__).resolve().parent.parent / "data" / "pois.json"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    async def get_dataset(self) -> CachedDataset:
        cached = self._read_cache()
        if cached and datetime.utcnow() - cached.cached_at < timedelta(minutes=self.settings.cache_ttl_minutes):
            return cached

        fresh = await self._build_dataset()
        self._write_cache(fresh)
        return fresh

    async def list_sites(
        self,
        q: str | None = None,
        district: str | None = None,
        municipality: str | None = None,
        water_category: str | None = None,
        bathing_water_type: str | None = None,
        water_quality: str | None = None,
        infrastructure: str | None = None,
        bbox: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
        radius_km: float | None = None,
    ) -> BathingSiteListResponse:
        dataset = await self.get_dataset()
        items = [site.model_copy(deep=True) for site in dataset.items]

        if q:
            query = q.casefold()
            items = [
                site
                for site in items
                if query
                in " ".join(
                    [
                        site.name,
                        site.municipality or "",
                        site.district or "",
                        site.region or "",
                    ]
                ).casefold()
            ]

        if district:
            items = [site for site in items if site.district == district]
        if municipality:
            items = [site for site in items if site.municipality == municipality]
        if water_category:
            items = [site for site in items if site.water_category == water_category]
        if bathing_water_type:
            items = [site for site in items if site.bathing_water_type == bathing_water_type]
        if water_quality:
            items = [site for site in items if site.water_quality == water_quality]
        if infrastructure:
            items = [site for site in items if infrastructure in site.infrastructure]

        if bbox:
            west, south, east, north = [float(part) for part in bbox.split(",")]
            items = [
                site
                for site in items
                if west <= site.coordinates.lon <= east and south <= site.coordinates.lat <= north
            ]

        if lat is not None and lon is not None:
            for site in items:
                site.distance_km = round(
                    _haversine_km(lat, lon, site.coordinates.lat, site.coordinates.lon), 2
                )
            if radius_km is not None:
                items = [site for site in items if site.distance_km is not None and site.distance_km <= radius_km]
            items.sort(key=lambda site: site.distance_km if site.distance_km is not None else 99999)

        filter_options = self._build_filters(dataset.items)
        return BathingSiteListResponse(
            items=items,
            total=len(items),
            filter_options=filter_options,
            data_updated_at=dataset.data_updated_at,
        )

    async def get_site(self, site_id: str) -> BathingSite | None:
        dataset = await self.get_dataset()
        for item in dataset.items:
            if item.id == site_id:
                return item
        return None

    async def health(self) -> dict[str, Any]:
        dataset = await self.get_dataset()
        age = int((datetime.utcnow() - dataset.cached_at).total_seconds())
        return {
            "status": "ok",
            "cache_age_seconds": age,
            "cached_at": dataset.cached_at,
            "source_urls": dataset.source_urls,
            "item_count": len(dataset.items),
        }

    async def get_map_items_by_bounds(
        self,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        item_type: str | None = None,
        category: str | None = None,
        infrastructure: str | None = None,
    ) -> MapFeatureCollection:
        items = await self._get_map_items(
            item_type=item_type,
            category=category,
            infrastructure=infrastructure,
        )
        bounded = [
            item for item in items
            if xmin <= item.lng <= xmax and ymin <= item.lat <= ymax
        ]
        return self._to_feature_collection(bounded, items)

    async def get_map_items_by_radius(
        self,
        lat: float,
        lng: float,
        radius_km: float | None = 25,
        item_type: str | None = None,
        category: str | None = None,
        infrastructure: str | None = None,
    ) -> MapFeatureCollection:
        items = await self._get_map_items(
            item_type=item_type,
            category=category,
            infrastructure=infrastructure,
        )
        nearby: list[MapItem] = []
        for item in items:
            distance = round(_haversine_km(lat, lng, item.lat, item.lng), 2)
            if radius_km is None or distance <= radius_km:
                nearby.append(item.model_copy(update={"distance_km": distance}))
        nearby.sort(key=lambda item: item.distance_km if item.distance_km is not None else 99999)
        return self._to_feature_collection(nearby, items)

    async def get_map_item_details(self, item_id: str | None = None, slug: str | None = None) -> MapItem | None:
        items = await self._get_map_items()
        for item in items:
            if item_id and item.id == item_id:
                return item
            if slug and item.slug == slug:
                return item
        return None

    async def _get_map_items(
        self,
        item_type: str | None = None,
        category: str | None = None,
        infrastructure: str | None = None,
    ) -> list[MapItem]:
        bathing_items = await self._get_bathing_map_items()
        poi_items = self._get_poi_items()
        items = bathing_items + poi_items

        if item_type in {"badestelle", "poi"}:
            items = [item for item in items if item.type == item_type]
        if category:
            items = [item for item in items if item.category == category]
        if infrastructure:
            items = [
                item for item in items
                if infrastructure in item.amenities or infrastructure == item.accessibility
            ]

        items.sort(key=lambda item: ((item.city or ""), (item.category or ""), item.title))
        return items

    async def _get_bathing_map_items(self) -> list[MapItem]:
        dataset = await self.get_dataset()
        items: list[MapItem] = []
        for site in dataset.items:
            last_update = None
            if site.last_sample_date:
                last_update = datetime.combine(site.last_sample_date, datetime.min.time())
            elif dataset.data_updated_at:
                last_update = dataset.data_updated_at

            description = site.bathing_spot_information or site.description or site.impacts_on_bathing_water
            category = site.bathing_water_type or site.water_category or "Badestelle"
            city = site.municipality or site.district
            address = ", ".join(part for part in [site.municipality, site.district] if part) or None

            tags = [
                *site.infrastructure,
                *[value for value in [site.water_category, site.coastal_water, site.region] if value],
            ]
            accessibility = self._derive_accessibility(site)
            amenities = self._derive_amenities(site, accessibility)

            items.append(
                MapItem(
                    id=f"badestelle-{site.id}",
                    slug=self._build_bathing_slug(site),
                    type="badestelle",
                    title=self._get_bathing_display_title(site),
                    description=description,
                    category=category,
                    lat=site.coordinates.lat,
                    lng=site.coordinates.lon,
                    address=address,
                    city=city,
                    image_url=None,
                    website=site.source_url,
                    tags=sorted({tag for tag in tags if tag}),
                    water_quality=site.water_quality,
                    accessibility=accessibility,
                    possible_pollutions=site.possible_pollutions,
                    seasonal_status=site.seasonal_status,
                    season_start=site.season_start,
                    season_end=site.season_end,
                    last_update=last_update,
                    district=site.district,
                    amenities=amenities,
                )
            )
        return items

    def _get_poi_items(self) -> list[MapItem]:
        if not self.poi_path.exists():
            return []
        payload = json.loads(self.poi_path.read_text(encoding="utf-8"))
        return [
            MapItem(
                **{
                    **item,
                    "last_update": _parse_datetime(item.get("last_update")),
                }
            )
            for item in payload
        ]

    def _to_feature_collection(self, visible_items: list[MapItem], all_items: list[MapItem]) -> MapFeatureCollection:
        features = [
            MapFeature(
                id=item.id,
                geometry=MapPointGeometry(coordinates=(item.lng, item.lat)),
                properties=MapFeatureProperties(
                    id=item.id,
                    slug=item.slug,
                    type=item.type,
                    title=item.title,
                    category=item.category,
                    city=item.city,
                    water_quality=item.water_quality,
                ),
            )
            for item in visible_items
        ]
        return MapFeatureCollection(
            features=features,
            filters=MapFilters(
                types=sorted({item.type for item in all_items}),
                categories=sorted({item.category for item in all_items if item.category}),
                cities=sorted({item.city for item in all_items if item.city}),
                tags=sorted({tag for item in all_items for tag in item.tags}),
                infrastructures=sorted(
                    {
                        infrastructure
                        for item in all_items
                        for infrastructure in ([*item.amenities, item.accessibility] if item.type == "badestelle" else [])
                        if infrastructure
                    }
                ),
            ),
            total=len(features),
        )

    def _build_bathing_slug(self, site: BathingSite) -> str:
        name_parts = _split_bathing_name_parts(site.name)
        region = _normalize_bathing_region(name_parts[0]) if name_parts else None
        title = self._get_bathing_display_title(site)
        location = _clean_text(site.municipality or site.district)

        slug_parts = [part for part in [region, title] if part]
        if location and not _is_redundant_slug_part(title, location):
            slug_parts.append(location)
        slug_parts.append(site.id)

        return _slugify("-".join(slug_parts))

    def _get_bathing_display_title(self, site: BathingSite) -> str:
        candidates = [
            site.common_name,
            site.short_name,
        ]
        for candidate in candidates:
            cleaned = _clean_text(candidate)
            if cleaned:
                return _normalize_bathing_title(cleaned.replace(";", " "))

        cleaned_name = _clean_text(site.name) or site.id
        parts = [part.strip() for part in cleaned_name.split(";") if part.strip()]
        if len(parts) >= 2:
            readable = parts[-1]
            if len(parts) >= 3 and parts[-2].casefold() not in readable.casefold():
                readable = f"{parts[-1]}, {parts[-2]}"
            return _normalize_bathing_title(readable)

        return _normalize_bathing_title(cleaned_name.replace(";", " "))

    def _derive_accessibility(self, site: BathingSite) -> str | None:
        relevant_infrastructure = [
            label for label in site.infrastructure
            if any(
                keyword in label.casefold()
                for keyword in [
                    "barriere",
                    "rollstuhl",
                    "rampe",
                    "steg",
                    "zugang",
                    "treppe",
                    "parken",
                    "gebühren",
                    "fußweg",
                    "parkplatz",
                ]
            )
        ]
        if relevant_infrastructure:
            return ", ".join(relevant_infrastructure)

        text_sources = [
            site.bathing_spot_information,
            site.description,
            site.impacts_on_bathing_water,
        ]
        for text in text_sources:
            if not text:
                continue
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for sentence in sentences:
                lowered = sentence.casefold()
                if any(
                    keyword in lowered
                    for keyword in [
                        "barriere",
                        "rollstuhl",
                        "rampe",
                        "steg",
                        "zugang",
                        "treppe",
                        "parken",
                        "erreichbar",
                        "fußweg",
                    ]
                ):
                    return sentence.strip()

        return None

    def _derive_amenities(self, site: BathingSite, accessibility: str | None) -> list[str]:
        amenities = list(site.infrastructure)
        if not accessibility:
            return amenities

        accessibility_labels = {
            part.strip()
            for part in accessibility.split(",")
            if part.strip()
        }
        return [
            amenity for amenity in amenities
            if amenity not in accessibility_labels
        ]

    def _build_filters(self, items: list[BathingSite]) -> FilterOptions:
        infrastructures = sorted({label for item in items for label in item.infrastructure})
        return FilterOptions(
            districts=_as_sorted_values([item.district for item in items]),
            municipalities=_as_sorted_values([item.municipality for item in items]),
            water_categories=_as_sorted_values([item.water_category for item in items]),
            coastal_waters=_as_sorted_values([item.coastal_water for item in items]),
            bathing_water_types=_as_sorted_values([item.bathing_water_type for item in items]),
            water_qualities=_as_sorted_values([item.water_quality for item in items]),
            infrastructures=infrastructures,
        )

    async def _build_dataset(self) -> CachedDataset:
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=True) as client:
            source_urls = await self._discover_source_urls(client)
            raw_stammdaten = await self._fetch_table(client, source_urls["stammdaten"], STAMMDATEN_COLUMNS)
            raw_einstufung = await self._fetch_table(client, source_urls["einstufung"], EINSTUFUNG_COLUMNS)
            raw_infra = await self._fetch_table(client, source_urls["infrastruktur"], INFRASTRUCTURE_COLUMNS)
            raw_saison = await self._fetch_table(client, source_urls["saison"], SAISON_COLUMNS)
            raw_messungen = await self._fetch_table(client, source_urls["messungen"], MEASUREMENT_COLUMNS)

        quality_by_id: dict[str, dict[str, Any]] = {}
        for row in raw_einstufung:
            site_id = row["bathing_water_id"]
            current = quality_by_id.get(site_id)
            new_to_year = int(row["to_year"]) if row["to_year"] else -1
            current_to_year = int(current["to_year"]) if current and current.get("to_year") else -1
            if current is None or new_to_year >= current_to_year:
                quality_by_id[site_id] = row

        infrastructure_by_id: dict[str, set[str]] = {}
        for row in raw_infra:
            site_id = row["bathing_water_id"]
            infrastructure_by_id.setdefault(site_id, set()).add(_clean_text(row["infrastructure_label"]) or "")

        season_by_id: dict[str, dict[str, Any]] = {}
        for row in raw_saison:
            site_id = row["bathing_water_id"]
            current = season_by_id.get(site_id)
            row_end = _parse_date(row["season_end"]) or date.min
            current_end = _parse_date(current["season_end"]) if current else date.min
            if current is None or row_end >= current_end:
                season_by_id[site_id] = row

        measurements_by_id: dict[str, date] = {}
        for row in raw_messungen:
            site_id = row["bathing_water_id"]
            sample_date = _parse_date(row["sample_date"])
            if sample_date is None:
                continue
            if site_id not in measurements_by_id or sample_date > measurements_by_id[site_id]:
                measurements_by_id[site_id] = sample_date

        items: list[BathingSite] = []
        for row in raw_stammdaten:
            lat = _parse_float(row["lat"])
            lon = _parse_float(row["lon"])
            site_id = row["bathing_water_id"]
            if lat is None or lon is None or not site_id:
                continue

            quality = quality_by_id.get(site_id, {})
            season = season_by_id.get(site_id, {})
            infrastructure = sorted([item for item in infrastructure_by_id.get(site_id, set()) if item])

            items.append(
                BathingSite(
                    id=site_id,
                    name=_clean_text(row["bathing_water_name"]) or site_id,
                    short_name=_clean_text(row["short_name"]),
                    common_name=_clean_text(row["common_name"]),
                    municipality=_clean_text(row["municipality"]),
                    district=_clean_text(row["district"]),
                    region=_clean_text(row["river_basin_district_name"]),
                    water_category=_clean_text(row["water_category"]),
                    coastal_water=_clean_text(row["coastal_water"]),
                    bathing_water_type=_clean_text(row["bathing_water_type"]),
                    bathing_spot_length_m=_parse_float(row["bathing_spot_length_m"]),
                    description=_clean_text(row["description"]),
                    bathing_spot_information=_clean_text(row["bathing_spot_information"]),
                    impacts_on_bathing_water=_clean_text(row["impacts_on_bathing_water"]),
                    possible_pollutions=_clean_text(row["possible_pollutions"]),
                    infrastructure=infrastructure,
                    water_quality=_clean_text(quality.get("water_quality")),
                    water_quality_from_year=int(quality["from_year"]) if quality.get("from_year") else None,
                    water_quality_to_year=int(quality["to_year"]) if quality.get("to_year") else None,
                    seasonal_status=_clean_text(season.get("seasonal_status")),
                    season_start=_parse_date(season.get("season_start")),
                    season_end=_parse_date(season.get("season_end")),
                    last_sample_date=measurements_by_id.get(site_id),
                    source_url=source_urls["stammdaten"],
                    source_dataset="Open-Data-Portal Schleswig-Holstein",
                    coordinates=SiteCoordinates(lat=lat, lon=lon),
                )
            )

        items.sort(key=lambda item: ((item.district or ""), (item.municipality or ""), item.name))
        return CachedDataset(
            items=items,
            data_updated_at=datetime.utcnow(),
            source_urls=source_urls,
            cached_at=datetime.utcnow(),
        )

    async def _discover_source_urls(self, client: httpx.AsyncClient) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, config in SOURCE_QUERIES.items():
            preferred_url = config.get("preferred_url")
            if preferred_url:
                result[key] = preferred_url
                continue
            try:
                response = await client.get(CKAN_API_URL, params={"q": config["term"], "rows": 10})
                response.raise_for_status()
                payload = response.json()
                datasets = payload.get("result", {}).get("results", [])
                matching = [
                    dataset for dataset in datasets
                    if config["title"] in dataset.get("title", "")
                ]
                matching.sort(key=lambda dataset: dataset.get("metadata_modified", ""), reverse=True)
                resource_url = None
                for dataset in matching:
                    for resource in dataset.get("resources", []):
                        if resource.get("format", "").upper() == "CSV" and resource.get("url"):
                            resource_url = resource["url"]
                            break
                    if resource_url:
                        break
                result[key] = resource_url or config["fallback_url"]
            except Exception:
                result[key] = config["fallback_url"]
        return result

    async def _fetch_table(
        self,
        client: httpx.AsyncClient,
        url: str,
        fieldnames: list[str],
    ) -> list[dict[str, str]]:
        response = await client.get(url)
        response.raise_for_status()
        content = response.content

        # Some CKAN-exported bathing-water CSV files are already corrupted and contain
        # replacement characters. The direct EFI export still exposes the original bytes.
        if "\ufffd".encode("utf-8") in content and "badegewasser-stammdaten.csv" in url:
            retry_url = SOURCE_QUERIES["stammdaten"]["fallback_url"]
            retry_response = await client.get(retry_url)
            retry_response.raise_for_status()
            content = retry_response.content

        text: str
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("cp1252")
            except UnicodeDecodeError:
                text = content.decode("latin-1")

        reader = csv.reader(io.StringIO(text), delimiter="|", quotechar='"')
        rows: list[dict[str, str]] = []
        for raw_row in reader:
            if not raw_row:
                continue
            row = list(raw_row[: len(fieldnames)])
            if len(row) < len(fieldnames):
                row.extend([""] * (len(fieldnames) - len(row)))
            rows.append(dict(zip(fieldnames, row, strict=False)))
        return rows

    def _read_cache(self) -> CachedDataset | None:
        if not self.cache_path.exists():
            return None
        payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        items = [BathingSite.model_validate(item) for item in payload["items"]]
        return CachedDataset(
            items=items,
            data_updated_at=datetime.fromisoformat(payload["data_updated_at"]),
            source_urls=payload["source_urls"],
            cached_at=datetime.fromisoformat(payload["cached_at"]),
        )

    def _write_cache(self, dataset: CachedDataset) -> None:
        payload = {
            "items": [item.model_dump(mode="json") for item in dataset.items],
            "data_updated_at": dataset.data_updated_at.isoformat(),
            "source_urls": dataset.source_urls,
            "cached_at": dataset.cached_at.isoformat(),
        }
        self.cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
