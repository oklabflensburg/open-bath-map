from __future__ import annotations

import csv
import gzip
import io
import json
import re
import unicodedata
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from collections.abc import Callable

import httpx

from app.config import Settings, get_settings
from app.models.bathing_site import BathingSite, SiteCoordinates
from app.models.map_item import MapFeature, MapFeatureCollection, MapFeatureProperties, MapFilters, MapItem, MapItemSearchResponse, MapPointGeometry
from app.services.postgres_store import PostgresStore

from .constants import (
    CKAN_API_URL,
    EINSTUFUNG_COLUMNS,
    INFRASTRUCTURE_COLUMNS,
    MEASUREMENT_COLUMNS,
    POI_EXCLUDE_KEYWORDS,
    POI_INCLUDE_KEYWORDS,
    POI_SOURCE_QUERY,
    SAISON_COLUMNS,
    SOURCE_QUERIES,
    STAMMDATEN_COLUMNS,
)
from .dataset import CachedDataset
from .utils import (
    build_bathing_image_url,
    build_bathing_profile_url,
    clean_text,
    haversine_km,
    is_redundant_slug_part,
    normalize_bathing_coordinates,
    normalize_bathing_region,
    normalize_bathing_title,
    parse_date,
    parse_datetime,
    parse_float,
    slugify,
    split_bathing_name_parts,
)
from .wiki import WikiEnricher

DATASET_CACHE_VERSION = 2
PROFILE_LINK_CHECK_USER_AGENT = "OpenBathMap/0.1 (https://github.com/oklabflensburg/open-bath-map)"


class OpenDataService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.cache_path = Path(self.settings.cache_dir) / "bathing-sites-cache.json"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.postgres = PostgresStore(self.settings)
        self.wiki = WikiEnricher(self.settings)

    async def get_dataset(self) -> CachedDataset:
        cached = self._read_cache()
        if cached and datetime.utcnow() - cached.cached_at < timedelta(minutes=self.settings.cache_ttl_minutes):
            return cached

        fresh = await self._build_dataset()
        self._write_cache(fresh)
        return fresh

    async def health(self) -> dict[str, Any]:
        if self.postgres.is_enabled:
            await self.postgres.ensure_seeded(self.sync_database)
            return await self.postgres.health()
        dataset = await self.get_dataset()
        age = int((datetime.utcnow() - dataset.cached_at).total_seconds())
        return {
            "status": "ok",
            "cache_age_seconds": age,
            "cached_at": dataset.cached_at,
            "source_urls": dataset.source_urls,
            "item_count": len(dataset.items) + len(dataset.poi_items),
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
        if self.postgres.is_enabled:
            await self.postgres.ensure_seeded(self.sync_database)
            return await self.postgres.get_map_items_by_bounds(
                xmin=xmin,
                ymin=ymin,
                xmax=xmax,
                ymax=ymax,
                item_type=item_type,
                category=category,
                infrastructure=infrastructure,
            )
        items = await self._get_map_items(item_type=item_type, category=category, infrastructure=infrastructure)
        bounded = [item for item in items if xmin <= item.lng <= xmax and ymin <= item.lat <= ymax]
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
        if self.postgres.is_enabled:
            await self.postgres.ensure_seeded(self.sync_database)
            return await self.postgres.get_map_items_by_radius(
                lat=lat,
                lng=lng,
                radius_km=radius_km,
                item_type=item_type,
                category=category,
                infrastructure=infrastructure,
            )
        items = await self._get_map_items(item_type=item_type, category=category, infrastructure=infrastructure)
        nearby: list[MapItem] = []
        for item in items:
            distance = round(haversine_km(lat, lng, item.lat, item.lng), 2)
            if radius_km is None or distance <= radius_km:
                nearby.append(item.model_copy(update={"distance_km": distance}))
        nearby.sort(key=lambda item: item.distance_km if item.distance_km is not None else 99999)
        return self._to_feature_collection(nearby, items)

    async def get_map_item_details(self, item_id: str | None = None, slug: str | None = None) -> MapItem | None:
        if self.postgres.is_enabled:
            await self.postgres.ensure_seeded(self.sync_database)
            item = await self.postgres.get_map_item_details(item_id=item_id, slug=slug)
            item = await self._filter_invalid_bathing_profile_url(item)
            return await self._enrich_item_details(item)
        items = await self._get_map_items()
        for item in items:
            if item_id and item.id == item_id:
                item = await self._filter_invalid_bathing_profile_url(item)
                return await self._enrich_item_details(item)
            if slug and item.slug == slug:
                item = await self._filter_invalid_bathing_profile_url(item)
                return await self._enrich_item_details(item)
        return None

    async def _filter_invalid_bathing_profile_url(self, item: MapItem | None) -> MapItem | None:
        if item is None or item.type != "badestelle" or not item.bathing_profile_url:
            return item
        if await self._is_http_200(item.bathing_profile_url):
            return item
        return item.model_copy(update={"bathing_profile_url": None})

    async def _is_http_200(self, url: str) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=self.settings.request_timeout_seconds,
                headers={"User-Agent": PROFILE_LINK_CHECK_USER_AGENT},
                follow_redirects=True,
            ) as client:
                async with client.stream("GET", url) as response:
                    return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def _enrich_item_details(self, item: MapItem | None) -> MapItem | None:
        if item is None:
            return None
        try:
            return await self.wiki.enrich_item(item)
        except httpx.HTTPError:
            return item

    async def search_map_items(
        self,
        q: str,
        item_type: str | None = None,
        category: str | None = None,
        infrastructure: str | None = None,
        limit: int = 20,
    ) -> MapItemSearchResponse:
        if self.postgres.is_enabled:
            await self.postgres.ensure_seeded(self.sync_database)
            return await self.postgres.search_map_items(
                q=q,
                item_type=item_type,
                category=category,
                infrastructure=infrastructure,
                limit=limit,
            )

        items = await self._get_map_items(item_type=item_type, category=category, infrastructure=infrastructure)
        query = self._normalize_search_text(q)
        query_terms = [term for term in query.split(" ") if term]
        matches = []
        for item in items:
            haystack = self._normalize_search_text(
                " ".join(
                    filter(
                        None,
                        [
                            item.title,
                            item.description,
                            item.category,
                            item.city,
                            item.address,
                            item.district,
                            " ".join(item.tags),
                        ],
                    ),
                ),
            )
            if query in haystack:
                matches.append(item)
                continue
            haystack_tokens = haystack.split()
            if query_terms and all(
                term in haystack or any(self._is_fuzzy_match(term, token) for token in haystack_tokens)
                for term in query_terms
            ):
                matches.append(item)
        return MapItemSearchResponse(items=matches[:limit], total=len(matches))

    async def list_map_items(
        self,
        *,
        item_type: str | None = None,
        category: str | None = None,
        infrastructure: str | None = None,
        limit: int = 5000,
    ) -> MapItemSearchResponse:
        if self.postgres.is_enabled:
            await self.postgres.ensure_seeded(self.sync_database)
            return await self.postgres.list_map_items(
                item_type=item_type,
                category=category,
                infrastructure=infrastructure,
                limit=limit,
            )
        items = await self._get_map_items(
            item_type=item_type,
            category=category,
            infrastructure=infrastructure,
        )
        return MapItemSearchResponse(items=items[:limit], total=len(items))

    async def sync_database(
        self,
        progress: Callable[[str], None] | None = None,
    ) -> dict[str, int]:
        if not self.postgres.is_enabled:
            raise RuntimeError("DATABASE_URL is not configured")
        if progress:
            progress("Baue Open-Data-Datensatz auf")
        dataset = await self._build_dataset(progress=progress)
        if progress:
            progress(f"Datensatz geladen: {len(dataset.items)} Badestellen, {len(dataset.poi_items)} POIs")
            progress("Erzeuge Kartenobjekte für Badestellen")
        bathing_map_items = await self._get_bathing_map_items(dataset)
        if progress:
            progress("Reichere POIs mit Wikipedia/Wikidata an")
        dataset.poi_items = await self.wiki.enrich_items_with_progress(
            dataset.poi_items,
            progress=progress,
            label="POIs",
        )
        if progress:
            progress("Reichere Badestellen mit Wikipedia/Wikidata an")
        bathing_map_items = await self.wiki.enrich_items_with_progress(
            bathing_map_items,
            progress=progress,
            label="Badestellen",
        )
        if progress:
            progress("Schreibe Datensatz nach PostgreSQL")
        await self.postgres.save_dataset(dataset, bathing_map_items)
        if progress:
            progress("PostgreSQL-Sync abgeschlossen")
        return {
            "bathing_sites": len(dataset.items),
            "poi_items": len(dataset.poi_items),
        }

    async def _get_map_items(
        self,
        item_type: str | None = None,
        category: str | None = None,
        infrastructure: str | None = None,
    ) -> list[MapItem]:
        dataset = await self.get_dataset()
        bathing_items = await self._get_bathing_map_items(dataset)
        poi_items = [item.model_copy(deep=True) for item in dataset.poi_items]
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

    @staticmethod
    def _normalize_search_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", normalized.lower()).strip()

    @staticmethod
    def _is_fuzzy_match(query: str, token: str) -> bool:
        if len(query) < 4 or len(token) < 4:
            return False
        if abs(len(query) - len(token)) > 2:
            return False
        mismatches = sum(1 for left, right in zip(query, token) if left != right) + abs(len(query) - len(token))
        return mismatches <= 2

    async def _get_bathing_map_items(self, dataset: CachedDataset) -> list[MapItem]:
        items: list[MapItem] = []
        for site in dataset.items:
            last_update = datetime.combine(site.last_sample_date, datetime.min.time()) if site.last_sample_date else dataset.data_updated_at
            description = site.bathing_spot_information or site.description or site.impacts_on_bathing_water
            category = site.bathing_water_type or site.water_category or "Badestelle"
            city = site.municipality or site.district
            address = ", ".join(part for part in [site.municipality, site.district] if part) or None
            tags = [*site.infrastructure, *[value for value in [site.water_category, site.coastal_water, site.region] if value]]
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
                    municipality=site.municipality,
                    image_url=build_bathing_image_url(site.id, site.district),
                    bathing_profile_url=build_bathing_profile_url(site.id, site.district),
                    website=None,
                    tags=sorted({tag for tag in tags if tag}),
                    water_quality=site.water_quality,
                    accessibility=accessibility,
                    possible_pollutions=site.possible_pollutions,
                    seasonal_status=site.seasonal_status,
                    season_start=site.season_start,
                    season_end=site.season_end,
                    sample_type=site.sample_type,
                    intestinal_enterococci=site.intestinal_enterococci,
                    e_coli=site.e_coli,
                    water_temperature_c=site.water_temperature_c,
                    air_temperature_c=site.air_temperature_c,
                    transparency_m=site.transparency_m,
                    last_update=last_update,
                    district=site.district,
                    amenities=amenities,
                )
            )
        return await self.wiki.enrich_items(items)

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
                    },
                ),
            ),
            total=len(features),
        )

    def _build_bathing_slug(self, site: BathingSite) -> str:
        name_parts = split_bathing_name_parts(site.name)
        region = normalize_bathing_region(name_parts[0]) if name_parts else None
        title = self._get_bathing_display_title(site)
        location = clean_text(site.municipality or site.district)

        slug_parts = [part for part in [region, title] if part]
        if location and not is_redundant_slug_part(title, location):
            slug_parts.append(location)
        slug_parts.append(site.id)
        return slugify("-".join(slug_parts))

    def _get_bathing_display_title(self, site: BathingSite) -> str:
        for candidate in [site.common_name, site.short_name]:
            cleaned = clean_text(candidate)
            if cleaned:
                return normalize_bathing_title(cleaned.replace(";", " "))

        cleaned_name = clean_text(site.name) or site.id
        parts = [part.strip() for part in cleaned_name.split(";") if part.strip()]
        if len(parts) >= 2:
            readable = parts[-1]
            if len(parts) >= 3 and parts[-2].casefold() not in readable.casefold():
                readable = f"{parts[-1]}, {parts[-2]}"
            return normalize_bathing_title(readable)
        return normalize_bathing_title(cleaned_name.replace(";", " "))

    def _derive_accessibility(self, site: BathingSite) -> str | None:
        relevant_infrastructure = [
            label for label in site.infrastructure
            if any(keyword in label.casefold() for keyword in [
                "barriere", "rollstuhl", "rampe", "steg", "zugang", "treppe",
                "parken", "gebühren", "fußweg", "parkplatz",
            ])
        ]
        if relevant_infrastructure:
            return ", ".join(relevant_infrastructure)

        for text in [site.bathing_spot_information, site.description, site.impacts_on_bathing_water]:
            if not text:
                continue
            for sentence in re.split(r"(?<=[.!?])\s+", text):
                lowered = sentence.casefold()
                if any(keyword in lowered for keyword in [
                    "barriere", "rollstuhl", "rampe", "steg", "zugang",
                    "treppe", "parken", "erreichbar", "fußweg",
                ]):
                    return sentence.strip()
        return None

    def _derive_amenities(self, site: BathingSite, accessibility: str | None) -> list[str]:
        amenities = list(site.infrastructure)
        if not accessibility:
            return amenities
        accessibility_labels = {part.strip() for part in accessibility.split(",") if part.strip()}
        return [amenity for amenity in amenities if amenity not in accessibility_labels]

    def _is_relevant_tourism_poi(self, text_blob: str, title: str) -> bool:
        lowered_title = title.casefold()
        if not any(keyword in text_blob for keyword in POI_INCLUDE_KEYWORDS):
            return False
        if any(keyword in lowered_title for keyword in POI_EXCLUDE_KEYWORDS):
            return False
        if any(keyword in text_blob for keyword in ["parkplatz", "haltestelle"]):
            return False
        return True

    def _categorize_tourism_poi(self, text_blob: str) -> str:
        rules = [
            ("Seebrücke", ["seebrücke", "seebruecke"]),
            ("Promenade", ["strandpromenade", "promenade"]),
            ("Hafen", ["hafen", "marina"]),
            ("Strand", ["strand"]),
            ("Aussichtspunkt", ["aussichtspunkt", "aussicht", "ufer"]),
            ("Badestelle", ["badestelle", "naturbad"]),
            ("Schifffahrt", ["schiff", "fähre", "faehre", "anleger"]),
            ("Wassersport", ["wassersport"]),
        ]
        for label, keywords in rules:
            if any(keyword in text_blob for keyword in keywords):
                return label
        return "POI"

    def _build_tourism_tags(self, text_blob: str, category: str) -> list[str]:
        tags = {category.casefold()}
        keyword_map = {
            "strand": "strand",
            "hafen": "hafen",
            "promenade": "promenade",
            "ufer": "ufer",
            "kanal": "kanal",
            "förde": "förde",
            "foerde": "förde",
            "see": "see",
            "meer": "meer",
            "wassersport": "wassersport",
            "aussicht": "aussicht",
            "seebrücke": "seebrücke",
            "seebruecke": "seebrücke",
        }
        for keyword, tag in keyword_map.items():
            if keyword in text_blob:
                tags.add(tag)
        return sorted(tags)

    def _extract_opening_hours(self, raw_item: dict[str, Any]) -> str | None:
        for wrapper in raw_item.get("openingHoursInformations", []):
            info = wrapper.get("openingHoursInformation") or {}
            if info.get("permanentlyOpen"):
                return "Jederzeit zugänglich"
            if info.get("temporarilyClosed"):
                return "Vorübergehend geschlossen"
            if info.get("permanentlyClosed"):
                return "Dauerhaft geschlossen"
        return None

    def _extract_image_url(self, raw_item: dict[str, Any]) -> str | None:
        media = raw_item.get("media") or []
        candidates: list[str] = []

        def visit(value: Any) -> None:
            if isinstance(value, str):
                normalized = value.strip()
                lowered = normalized.casefold()
                if lowered.startswith("//"):
                    normalized = f"https:{normalized}"
                    lowered = normalized.casefold()
                if lowered.startswith(("http://", "https://")) and any(
                    token in lowered for token in [".jpg", ".jpeg", ".png", ".webp", ".gif", "/image", "image/"]
                ):
                    candidates.append(normalized)
                return

            if isinstance(value, dict):
                for nested in value.values():
                    visit(nested)
                return

            if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
                for nested in value:
                    visit(nested)

        visit(media)
        return candidates[0] if candidates else None

    def _map_tourism_poi(self, raw_item: dict[str, Any]) -> MapItem | None:
        geo_info = raw_item.get("geoInfo") or {}
        coordinates = geo_info.get("coordinates") or {}
        lat = parse_float(coordinates.get("latitude"))
        lng = parse_float(coordinates.get("longitude"))
        if lat is None or lng is None:
            return None

        title = clean_text((raw_item.get("title") or {}).get("de"))
        if not title:
            return None

        short_description = clean_text((raw_item.get("shortDescription") or {}).get("de"))
        long_description = clean_text((raw_item.get("longDescription") or {}).get("de"))
        permalink = clean_text((raw_item.get("permaLink") or {}).get("de")) or str(raw_item.get("id") or "")
        address_data = (raw_item.get("contact1") or {}).get("address") or {}
        city = clean_text(geo_info.get("city") or address_data.get("city"))
        postcode = clean_text(geo_info.get("zipcode") or address_data.get("zipcode"))
        street = clean_text(geo_info.get("street") or address_data.get("street"))
        street_no = clean_text(geo_info.get("streetNo") or address_data.get("streetNo"))
        website = clean_text((address_data.get("homepage") or {}).get("de"))
        last_update = parse_datetime(raw_item.get("lastChangeTime"))
        content_license = clean_text(((raw_item.get("mediaLicense") or {}).get("i18nName") or {}).get("de"))
        image_url = self._extract_image_url(raw_item)

        text_blob = " ".join(filter(None, [title, short_description, long_description, permalink])).casefold()
        if not self._is_relevant_tourism_poi(text_blob, title):
            return None

        address = " ".join(part for part in [street, street_no] if part) or None
        category = self._categorize_tourism_poi(text_blob)

        return MapItem(
            id=f"poi-{raw_item.get('id')}",
            slug=slugify(permalink or title),
            type="poi",
            title=title,
            description=short_description or long_description,
            category=category,
            lat=lat,
            lng=lng,
            address=address,
            postcode=postcode,
            city=city,
            municipality=city,
            image_url=image_url,
            website=website,
            source_name="Touristische Landesdatenbank Schleswig-Holstein (TA.SH)",
            content_license=content_license,
            tags=self._build_tourism_tags(text_blob, category),
            last_update=last_update,
            opening_hours=self._extract_opening_hours(raw_item),
            amenities=[],
        )

    async def _build_dataset(
        self,
        progress: Callable[[str], None] | None = None,
    ) -> CachedDataset:
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds, follow_redirects=True) as client:
            if progress:
                progress("Ermittle Quell-URLs für Badegewässer")
            source_urls = await self._discover_source_urls(client)
            if progress:
                progress("Ermittle Quell-URL für touristische POIs")
            poi_source_url = await self._discover_poi_source_url(client)
            if progress:
                progress("Lade CSV: Stammdaten")
            raw_stammdaten = await self._fetch_table(client, source_urls["stammdaten"], STAMMDATEN_COLUMNS)
            if progress:
                progress(f"Stammdaten geladen: {len(raw_stammdaten)} Zeilen")
                progress("Lade CSV: Einstufung")
            raw_einstufung = await self._fetch_table(client, source_urls["einstufung"], EINSTUFUNG_COLUMNS)
            if progress:
                progress(f"Einstufung geladen: {len(raw_einstufung)} Zeilen")
                progress("Lade CSV: Infrastruktur")
            raw_infra = await self._fetch_table(client, source_urls["infrastruktur"], INFRASTRUCTURE_COLUMNS)
            if progress:
                progress(f"Infrastruktur geladen: {len(raw_infra)} Zeilen")
                progress("Lade CSV: Saisondauer")
            raw_saison = await self._fetch_table(client, source_urls["saison"], SAISON_COLUMNS)
            if progress:
                progress(f"Saisondauer geladen: {len(raw_saison)} Zeilen")
                progress("Lade CSV: Messungen")
            raw_messungen = await self._fetch_table(client, source_urls["messungen"], MEASUREMENT_COLUMNS)
            if progress:
                progress(f"Messungen geladen: {len(raw_messungen)} Zeilen")
                progress("Lade POI-JSON")
            poi_items = await self._fetch_poi_items(client, poi_source_url)
            if progress:
                progress(f"POIs geladen: {len(poi_items)} Einträge")

        if progress:
            progress("Starte Wiki-Enrichment für POIs im Datensatzaufbau")
        poi_items = await self.wiki.enrich_items_with_progress(
            poi_items,
            progress=progress,
            label="POIs (Build)",
        )

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
            infrastructure_by_id.setdefault(site_id, set()).add(clean_text(row["infrastructure_label"]) or "")

        season_by_id: dict[str, dict[str, Any]] = {}
        for row in raw_saison:
            site_id = row["bathing_water_id"]
            current = season_by_id.get(site_id)
            row_end = parse_date(row["season_end"]) or date.min
            current_end = parse_date(current["season_end"]) if current else date.min
            if current is None or row_end >= current_end:
                season_by_id[site_id] = row

        measurements_by_id: dict[str, dict[str, Any]] = {}
        for row in raw_messungen:
            site_id = row["bathing_water_id"]
            sample_date = parse_date(row["sample_date"])
            measurement_id = clean_text(row.get("measurement_id"))
            if sample_date is None or not site_id:
                continue
            previous = measurements_by_id.get(site_id)
            if previous:
                previous_date = previous.get("sample_date")
                previous_measurement_id = previous.get("measurement_id") or ""
                if isinstance(previous_date, date):
                    if sample_date < previous_date:
                        continue
                    if sample_date == previous_date and (measurement_id or "") <= previous_measurement_id:
                        continue

            measurements_by_id[site_id] = {
                "sample_date": sample_date,
                "measurement_id": measurement_id,
                "sample_type": clean_text(row.get("sample_type")),
                "intestinal_enterococci": parse_float(row.get("intestinal_enterococci")),
                "e_coli": parse_float(row.get("e_coli")),
                "water_temperature_c": parse_float(row.get("water_temperature_c")),
                "air_temperature_c": parse_float(row.get("air_temperature_c")),
                "transparency_m": parse_float(row.get("transparency_m")),
            }

        items: list[BathingSite] = []
        for row in raw_stammdaten:
            utm_east = parse_float(row["utm_east"])
            utm_north = parse_float(row["utm_north"])
            raw_lon = parse_float(row["lon"])
            raw_lat = parse_float(row["lat"])
            lon, lat = normalize_bathing_coordinates(
                utm_east=utm_east,
                utm_north=utm_north,
                lon=raw_lon,
                lat=raw_lat,
            )
            site_id = row["bathing_water_id"]
            if lat is None or lon is None or not site_id:
                continue

            quality = quality_by_id.get(site_id, {})
            season = season_by_id.get(site_id, {})
            measurement = measurements_by_id.get(site_id, {})
            infrastructure = sorted([item for item in infrastructure_by_id.get(site_id, set()) if item])

            items.append(
                BathingSite(
                    id=site_id,
                    name=clean_text(row["bathing_water_name"]) or site_id,
                    short_name=clean_text(row["short_name"]),
                    common_name=clean_text(row["common_name"]),
                    municipality=clean_text(row["municipality"]),
                    district=clean_text(row["district"]),
                    region=clean_text(row["river_basin_district_name"]),
                    water_category=clean_text(row["water_category"]),
                    coastal_water=clean_text(row["coastal_water"]),
                    bathing_water_type=clean_text(row["bathing_water_type"]),
                    bathing_spot_length_m=parse_float(row["bathing_spot_length_m"]),
                    description=clean_text(row["description"]),
                    bathing_spot_information=clean_text(row["bathing_spot_information"]),
                    impacts_on_bathing_water=clean_text(row["impacts_on_bathing_water"]),
                    possible_pollutions=clean_text(row["possible_pollutions"]),
                    infrastructure=infrastructure,
                    water_quality=clean_text(quality.get("water_quality")),
                    water_quality_from_year=int(quality["from_year"]) if quality.get("from_year") else None,
                    water_quality_to_year=int(quality["to_year"]) if quality.get("to_year") else None,
                    seasonal_status=clean_text(season.get("seasonal_status")),
                    season_start=parse_date(season.get("season_start")),
                    season_end=parse_date(season.get("season_end")),
                    last_sample_date=measurement.get("sample_date"),
                    sample_type=measurement.get("sample_type"),
                    intestinal_enterococci=measurement.get("intestinal_enterococci"),
                    e_coli=measurement.get("e_coli"),
                    water_temperature_c=measurement.get("water_temperature_c"),
                    air_temperature_c=measurement.get("air_temperature_c"),
                    transparency_m=measurement.get("transparency_m"),
                    source_url=source_urls["stammdaten"],
                    source_dataset="Open-Data-Portal Schleswig-Holstein",
                    coordinates=SiteCoordinates(lat=lat, lon=lon),
                )
            )

        items.sort(key=lambda item: ((item.district or ""), (item.municipality or ""), item.name))
        if progress:
            progress(f"Badestellen normalisiert: {len(items)} Einträge")
        return CachedDataset(
            items=items,
            poi_items=poi_items,
            data_updated_at=datetime.utcnow(),
            source_urls={**source_urls, "pois": poi_source_url},
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
                matching = [dataset for dataset in datasets if config["title"] in dataset.get("title", "")]
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

    async def _discover_poi_source_url(self, client: httpx.AsyncClient) -> str:
        response = await client.get(
            CKAN_API_URL,
            params={"q": POI_SOURCE_QUERY["term"], "rows": 10},
        )
        response.raise_for_status()
        payload = response.json()
        datasets = payload.get("result", {}).get("results", [])
        matching = [
            dataset for dataset in datasets
            if POI_SOURCE_QUERY["title"] in dataset.get("title", "")
        ]
        matching.sort(key=lambda dataset: dataset.get("metadata_modified", ""), reverse=True)

        for dataset in matching:
            resources = dataset.get("resources", [])
            json_resources = [
                resource for resource in resources
                if resource.get("url") and resource.get("format", "").upper() == "JSON"
            ]
            json_resources.sort(
                key=lambda resource: (
                    "poi" not in (resource.get("name", "") or "").casefold(),
                    ".gz" not in (resource.get("url", "") or "").casefold(),
                ),
            )
            for resource in json_resources:
                url = resource.get("url")
                if url:
                    return url

        raise RuntimeError("Could not discover current TA.SH POI JSON resource URL")

    async def _fetch_table(self, client: httpx.AsyncClient, url: str, fieldnames: list[str]) -> list[dict[str, str]]:
        response = await client.get(url)
        response.raise_for_status()
        content = response.content

        if "\ufffd".encode("utf-8") in content and "badegewasser-stammdaten.csv" in url:
            retry_url = SOURCE_QUERIES["stammdaten"]["fallback_url"]
            retry_response = await client.get(retry_url)
            retry_response.raise_for_status()
            content = retry_response.content

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

    async def _fetch_poi_items(self, client: httpx.AsyncClient, url: str) -> list[MapItem]:
        response = await client.get(url)
        response.raise_for_status()
        content = response.content
        if content[:2] == b"\x1f\x8b":
            content = gzip.decompress(content)
        payload = json.loads(content)
        if not isinstance(payload, list):
            return []

        items = [item for raw_item in payload if (item := self._map_tourism_poi(raw_item)) is not None]
        items.sort(key=lambda item: ((item.city or ""), (item.category or ""), item.title))
        return items

    def _read_cache(self) -> CachedDataset | None:
        if not self.cache_path.exists():
            return None
        payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        if payload.get("cache_version") != DATASET_CACHE_VERSION:
            return None
        if "poi_items" not in payload:
            return None
        return CachedDataset(
            items=[BathingSite.model_validate(item) for item in payload["items"]],
            poi_items=[MapItem.model_validate(item) for item in payload.get("poi_items", [])],
            data_updated_at=datetime.fromisoformat(payload["data_updated_at"]),
            source_urls=payload["source_urls"],
            cached_at=datetime.fromisoformat(payload["cached_at"]),
        )

    def _write_cache(self, dataset: CachedDataset) -> None:
        payload = {
            "cache_version": DATASET_CACHE_VERSION,
            "items": [item.model_dump(mode="json") for item in dataset.items],
            "poi_items": [item.model_dump(mode="json") for item in dataset.poi_items],
            "data_updated_at": dataset.data_updated_at.isoformat(),
            "source_urls": dataset.source_urls,
            "cached_at": dataset.cached_at.isoformat(),
        }
        self.cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
