from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Awaitable, Callable

from geoalchemy2 import Geography, WKTElement
from sqlalchemy import and_, case, cast, delete, distinct, func, or_, select

from app.config import Settings, get_settings
from app.db.models import BathingSiteRecord, DatasetStateRecord, MapItemRecord
from app.db.session import create_session, dispose_engine, ensure_database_support_objects, get_database_url
from app.models.bathing_site import BathingSite, BathingSiteListResponse, FilterOptions, SiteCoordinates
from app.models.map_item import MapFeature, MapFeatureCollection, MapFeatureProperties, MapFilters, MapItem, MapItemSearchResponse, MapPointGeometry
from app.services.opendata.utils import build_bathing_image_url


class PostgresStore:
    _initialized = False

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def is_enabled(self) -> bool:
        return bool(self.settings.database_url)

    async def connect(self) -> None:
        if not self.is_enabled:
            return
        database_url = get_database_url(self.settings)
        if not database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        if not PostgresStore._initialized:
            await ensure_database_support_objects(self.settings)
            PostgresStore._initialized = True

    async def close(self) -> None:
        if PostgresStore._initialized:
            await dispose_engine()
            PostgresStore._initialized = False

    async def ensure_seeded(self, loader: Callable[[], Awaitable[Any]]) -> None:
        if not self.is_enabled:
            return
        await self.connect()
        async with create_session(self.settings) as session:
            state = await session.get(DatasetStateRecord, 1)
        if state is not None:
            return
        await loader()

    async def save_dataset(self, dataset: Any, bathing_map_items: list[MapItem] | None = None) -> None:
        await self.connect()
        if bathing_map_items is None:
            bathing_map_items = self._to_bathing_map_items(
                dataset.items, dataset.data_updated_at)
        async with create_session(self.settings) as session:
            async with session.begin():
                await session.execute(delete(BathingSiteRecord))
                await session.execute(delete(MapItemRecord))
                await session.execute(delete(DatasetStateRecord))
                session.add_all([BathingSiteRecord(
                    **self._bathing_site_params(item)) for item in dataset.items])
                session.add_all(
                    [MapItemRecord(**self._map_item_params(item))
                     for item in [*dataset.poi_items, *bathing_map_items]]
                )
                session.add(
                    DatasetStateRecord(
                        id=1,
                        data_updated_at=dataset.data_updated_at,
                        synced_at=dataset.cached_at,
                        source_urls=dataset.source_urls,
                    )
                )

    async def list_sites(
        self,
        *,
        q: str | None,
        district: str | None,
        municipality: str | None,
        water_category: str | None,
        bathing_water_type: str | None,
        water_quality: str | None,
        infrastructure: str | None,
        bbox: str | None,
        lat: float | None,
        lon: float | None,
        radius_km: float | None,
    ) -> BathingSiteListResponse:
        filters: list[Any] = []
        search_rank = None
        distance_expr = None

        if q:
            search_vector = func.to_tsvector(
                "german", BathingSiteRecord.search_text)
            search_query = func.websearch_to_tsquery("german", q)
            filters.append(search_vector.op("@@")(search_query))
            search_rank = func.ts_rank(search_vector, search_query)
        if district:
            filters.append(BathingSiteRecord.district == district)
        if municipality:
            filters.append(BathingSiteRecord.municipality == municipality)
        if water_category:
            filters.append(BathingSiteRecord.water_category == water_category)
        if bathing_water_type:
            filters.append(
                BathingSiteRecord.bathing_water_type == bathing_water_type)
        if water_quality:
            filters.append(BathingSiteRecord.water_quality == water_quality)
        if infrastructure:
            filters.append(
                BathingSiteRecord.infrastructure.any(infrastructure))
        if bbox:
            west, south, east, north = [
                float(part) for part in bbox.split(",")]
            filters.append(
                func.ST_Intersects(
                    BathingSiteRecord.geom,
                    func.ST_MakeEnvelope(west, south, east, north, 4326),
                )
            )
        if lat is not None and lon is not None:
            search_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
            distance_expr = func.ST_DistanceSphere(
                BathingSiteRecord.geom, search_point) / 1000
            if radius_km is not None:
                filters.append(
                    func.ST_DWithin(
                        cast(BathingSiteRecord.geom, Geography),
                        cast(search_point, Geography),
                        radius_km * 1000,
                    )
                )

        async with create_session(self.settings) as session:
            if distance_expr is not None:
                result = await session.exec(
                    select(BathingSiteRecord, distance_expr.label("distance_km"))
                    .where(*filters)
                    .order_by(distance_expr.nulls_last(), BathingSiteRecord.name)
                )
                items = [
                    self._record_to_bathing_site(self._unwrap_record(record)).model_copy(
                        update={"distance_km": distance_km_value})
                    for record, distance_km_value in result.all()
                ]
            else:
                statement = select(BathingSiteRecord).where(*filters)
                if search_rank is not None:
                    statement = statement.order_by(
                        search_rank.desc(), BathingSiteRecord.name)
                else:
                    statement = statement.order_by(
                        BathingSiteRecord.district.nulls_last(),
                        BathingSiteRecord.municipality.nulls_last(),
                        BathingSiteRecord.name,
                    )
                result = await session.exec(statement)
                items = [self._record_to_bathing_site(
                    self._unwrap_record(record)) for record in result.all()]

        filters = await self._build_filter_options()
        state = await self._get_dataset_state_record()
        return BathingSiteListResponse(
            items=items,
            total=len(items),
            filter_options=filters,
            data_updated_at=state.data_updated_at,
        )

    async def get_site(self, site_id: str) -> BathingSite | None:
        async with create_session(self.settings) as session:
            record = await session.get(BathingSiteRecord, site_id)
        return self._record_to_bathing_site(record) if record else None

    async def health(self) -> dict[str, Any]:
        state = await self._get_dataset_state_record()
        async with create_session(self.settings) as session:
            bathing_site_count = await session.scalar(
                select(func.count()).select_from(BathingSiteRecord)
            )
            poi_count = await session.scalar(
                select(func.count()).select_from(
                    MapItemRecord).where(MapItemRecord.type == "poi")
            )
        age = int(
            (datetime.utcnow() - state.synced_at.replace(tzinfo=None)).total_seconds())
        return {
            "status": "ok",
            "cache_age_seconds": age,
            "cached_at": state.synced_at,
            "source_urls": state.source_urls,
            "item_count": (bathing_site_count or 0) + (poi_count or 0),
        }

    async def get_map_items_by_bounds(
        self,
        *,
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        item_type: str | None,
        category: str | None,
        infrastructure: str | None,
    ) -> MapFeatureCollection:
        all_items = await self._query_map_items(
            item_type=item_type,
            category=category,
            infrastructure=infrastructure,
        )
        visible_items = [
            item for item in all_items
            if xmin <= item.lng <= xmax and ymin <= item.lat <= ymax
        ]
        return self._to_feature_collection(visible_items, all_items)

    async def get_map_items_by_radius(
        self,
        *,
        lat: float,
        lng: float,
        radius_km: float | None,
        item_type: str | None,
        category: str | None,
        infrastructure: str | None,
    ) -> MapFeatureCollection:
        filters: list[Any] = []
        if item_type in {"badestelle", "poi"}:
            filters.append(MapItemRecord.type == item_type)
        if category:
            filters.append(MapItemRecord.category == category)
        if infrastructure:
            filters.append(
                or_(
                    MapItemRecord.amenities.any(infrastructure),
                    MapItemRecord.accessibility == infrastructure,
                )
            )

        search_point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
        distance_expr = func.ST_DistanceSphere(MapItemRecord.geom, search_point) / 1000
        if radius_km is not None:
            filters.append(
                func.ST_DWithin(
                    cast(MapItemRecord.geom, Geography),
                    cast(search_point, Geography),
                    radius_km * 1000,
                )
            )

        async with create_session(self.settings) as session:
            result = await session.exec(
                select(MapItemRecord, distance_expr.label("distance_km"))
                .where(*filters)
                .order_by(distance_expr.nulls_last(), MapItemRecord.title)
            )
            visible_items = [
                self._record_to_map_item(self._unwrap_record(record)).model_copy(
                    update={"distance_km": distance_km_value})
                for record, distance_km_value in result.all()
            ]

        all_items = await self._query_map_items(
            item_type=item_type,
            category=category,
            infrastructure=infrastructure,
        )
        return self._to_feature_collection(visible_items, all_items)

    async def get_map_item_details(self, *, item_id: str | None, slug: str | None) -> MapItem | None:
        if not item_id and not slug:
            return None

        async with create_session(self.settings) as session:
            statement = select(MapItemRecord)
            if item_id:
                statement = statement.where(MapItemRecord.id == item_id)
            else:
                statement = statement.where(MapItemRecord.slug == slug)
            record = await session.scalar(statement)

        return self._record_to_map_item(record) if record else None

    async def search_map_items(
        self,
        *,
        q: str,
        item_type: str | None,
        category: str | None,
        infrastructure: str | None,
        limit: int,
    ) -> MapItemSearchResponse:
        normalized_query = self._normalize_search_text(q)
        search_terms = self._search_terms(q)
        filters: list[Any] = []
        if item_type in {"badestelle", "poi"}:
            filters.append(MapItemRecord.type == item_type)
        if category:
            filters.append(MapItemRecord.category == category)
        if infrastructure:
            filters.append(
                or_(
                    MapItemRecord.amenities.any(infrastructure),
                    MapItemRecord.accessibility == infrastructure,
                )
            )

        search_vector = func.to_tsvector("german", MapItemRecord.search_text)
        ts_query = func.plainto_tsquery("german", q)
        normalized_search = func.immutable_unaccent(
            func.lower(MapItemRecord.search_text))
        fts_match = search_vector.op("@@")(ts_query)

        if search_terms:
            term_predicates = [
                or_(
                    normalized_search.contains(term),
                    func.word_similarity(term, normalized_search) >= 0.6,
                )
                for term in search_terms
            ]
            filters.append(and_(fts_match, *term_predicates))
        else:
            filters.append(fts_match)

        search_rank = func.ts_rank(search_vector, ts_query)
        similarity_rank = func.similarity(normalized_search, normalized_query)
        word_similarity_rank = func.word_similarity(
            normalized_query, normalized_search)
        ordering_rank = func.greatest(
            search_rank, similarity_rank, word_similarity_rank)

        async with create_session(self.settings) as session:
            total = await session.scalar(
                select(func.count()).select_from(MapItemRecord).where(*filters)
            )
            result = await session.exec(
                select(MapItemRecord)
                .where(*filters)
                .order_by(
                    case((fts_match, 0), else_=1),
                    ordering_rank.desc(),
                    MapItemRecord.title,
                )
                .limit(limit)
            )
            items = [self._record_to_map_item(self._unwrap_record(record))
                     for record in result.all()]

        return MapItemSearchResponse(items=items, total=total or 0)

    async def _query_map_items(
        self,
        *,
        item_type: str | None,
        category: str | None,
        infrastructure: str | None,
    ) -> list[MapItem]:
        filters: list[Any] = []
        if item_type in {"badestelle", "poi"}:
            filters.append(MapItemRecord.type == item_type)
        if category:
            filters.append(MapItemRecord.category == category)
        if infrastructure:
            filters.append(
                or_(
                    MapItemRecord.amenities.any(infrastructure),
                    MapItemRecord.accessibility == infrastructure,
                )
            )

        async with create_session(self.settings) as session:
            result = await session.exec(
                select(MapItemRecord)
                .where(*filters)
                .order_by(
                    MapItemRecord.city.nulls_last(),
                    MapItemRecord.category.nulls_last(),
                    MapItemRecord.title,
                )
            )
            return [self._record_to_map_item(self._unwrap_record(record)) for record in result.all()]

    async def _build_filter_options(self) -> FilterOptions:
        async with create_session(self.settings) as session:
            districts = await session.exec(
                select(distinct(BathingSiteRecord.district))
                .where(BathingSiteRecord.district.is_not(None))
                .order_by(BathingSiteRecord.district)
            )
            municipalities = await session.exec(
                select(distinct(BathingSiteRecord.municipality))
                .where(BathingSiteRecord.municipality.is_not(None))
                .order_by(BathingSiteRecord.municipality)
            )
            water_categories = await session.exec(
                select(distinct(BathingSiteRecord.water_category))
                .where(BathingSiteRecord.water_category.is_not(None))
                .order_by(BathingSiteRecord.water_category)
            )
            coastal_waters = await session.exec(
                select(distinct(BathingSiteRecord.coastal_water))
                .where(BathingSiteRecord.coastal_water.is_not(None))
                .order_by(BathingSiteRecord.coastal_water)
            )
            bathing_water_types = await session.exec(
                select(distinct(BathingSiteRecord.bathing_water_type))
                .where(BathingSiteRecord.bathing_water_type.is_not(None))
                .order_by(BathingSiteRecord.bathing_water_type)
            )
            water_qualities = await session.exec(
                select(distinct(BathingSiteRecord.water_quality))
                .where(BathingSiteRecord.water_quality.is_not(None))
                .order_by(BathingSiteRecord.water_quality)
            )
            infrastructure_values = await session.exec(
                select(distinct(func.unnest(BathingSiteRecord.infrastructure)))
                .where(BathingSiteRecord.infrastructure.is_not(None))
                .order_by(func.unnest(BathingSiteRecord.infrastructure))
            )

            return FilterOptions(
                districts=[value for value in districts.all() if value],
                municipalities=[
                    value for value in municipalities.all() if value],
                water_categories=[
                    value for value in water_categories.all() if value],
                coastal_waters=[
                    value for value in coastal_waters.all() if value],
                bathing_water_types=[
                    value for value in bathing_water_types.all() if value],
                water_qualities=[
                    value for value in water_qualities.all() if value],
                infrastructures=[
                    value for value in infrastructure_values.all() if value],
            )

    async def _get_dataset_state(self) -> dict[str, Any]:
        state = await self._fetch_one("SELECT * FROM dataset_state WHERE id = 1")
        if state is None:
            raise RuntimeError(
                "PostgreSQL dataset is empty. Run the sync script or seed on first access.")
        return state

    async def _get_dataset_state_record(self) -> DatasetStateRecord:
        async with create_session(self.settings) as session:
            state = await session.get(DatasetStateRecord, 1)
        if state is None:
            raise RuntimeError(
                "PostgreSQL dataset is empty. Run the sync script or seed on first access.")
        return state

    async def _fetch_one(self, query: str, params: Any = ()) -> dict[str, Any] | None:
        await self.connect()
        async with create_session(self.settings) as session:
            connection = await session.connection()
            result = await connection.exec_driver_sql(query, tuple(params) if isinstance(params, list) else params)
            row = result.mappings().one_or_none()
            return dict(row) if row is not None else None

    async def _fetch_all(self, query: str, params: Any = ()) -> list[dict[str, Any]]:
        await self.connect()
        async with create_session(self.settings) as session:
            connection = await session.connection()
            result = await connection.exec_driver_sql(query, tuple(params) if isinstance(params, list) else params)
            return [dict(row) for row in result.mappings().all()]

    @staticmethod
    def _where_clause(where: list[str]) -> str:
        return f"WHERE {' AND '.join(where)}" if where else ""

    @staticmethod
    def _search_vector_sql() -> str:
        return "to_tsvector('german', search_text)"

    @staticmethod
    def _normalized_search_sql() -> str:
        return "immutable_unaccent(lower(search_text))"

    @staticmethod
    def _normalize_search_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode(
            "ascii", "ignore").decode("ascii")
        normalized = re.sub(r"\s+", " ", normalized.lower()).strip()
        return normalized

    @classmethod
    def _search_terms(cls, value: str) -> list[str]:
        return [term for term in cls._normalize_search_text(value).split(" ") if term]

    @staticmethod
    def _bathing_site_params(item: BathingSite) -> dict[str, Any]:
        return {
            **item.model_dump(),
            "lat": item.coordinates.lat,
            "lon": item.coordinates.lon,
            "geom": WKTElement(f"POINT({item.coordinates.lon} {item.coordinates.lat})", srid=4326),
            "search_text": " ".join(
                filter(
                    None,
                    [
                        item.name,
                        item.short_name,
                        item.common_name,
                        item.municipality,
                        item.district,
                        item.region,
                        item.description,
                        item.bathing_spot_information,
                    ],
                ),
            ),
        }

    @staticmethod
    def _map_item_params(item: MapItem) -> dict[str, Any]:
        return {
            **item.model_dump(),
            "geom": WKTElement(f"POINT({item.lng} {item.lat})", srid=4326),
            "search_text": " ".join(
                filter(
                    None,
                    [
                        item.title,
                        item.description,
                        item.category,
                        item.address,
                        item.city,
                        item.municipality,
                        item.district,
                        " ".join(item.tags),
                    ],
                ),
            ),
        }

    @staticmethod
    def _row_to_bathing_site(row: dict[str, Any]) -> BathingSite:
        return BathingSite(
            id=row["id"],
            name=row["name"],
            short_name=row["short_name"],
            common_name=row["common_name"],
            municipality=row["municipality"],
            district=row["district"],
            region=row["region"],
            water_category=row["water_category"],
            coastal_water=row["coastal_water"],
            bathing_water_type=row["bathing_water_type"],
            bathing_spot_length_m=row["bathing_spot_length_m"],
            description=row["description"],
            bathing_spot_information=row["bathing_spot_information"],
            impacts_on_bathing_water=row["impacts_on_bathing_water"],
            possible_pollutions=row["possible_pollutions"],
            infrastructure=row["infrastructure"] or [],
            water_quality=row["water_quality"],
            water_quality_from_year=row["water_quality_from_year"],
            water_quality_to_year=row["water_quality_to_year"],
            seasonal_status=row["seasonal_status"],
            season_start=row["season_start"],
            season_end=row["season_end"],
            last_sample_date=row["last_sample_date"],
            source_url=row["source_url"],
            source_dataset=row["source_dataset"],
            coordinates=SiteCoordinates(lat=row["lat"], lon=row["lon"]),
            distance_km=row.get("distance_km"),
        )

    @staticmethod
    def _record_to_bathing_site(record: BathingSiteRecord) -> BathingSite:
        return BathingSite(
            id=record.id,
            name=record.name,
            short_name=record.short_name,
            common_name=record.common_name,
            municipality=record.municipality,
            district=record.district,
            region=record.region,
            water_category=record.water_category,
            coastal_water=record.coastal_water,
            bathing_water_type=record.bathing_water_type,
            bathing_spot_length_m=record.bathing_spot_length_m,
            description=record.description,
            bathing_spot_information=record.bathing_spot_information,
            impacts_on_bathing_water=record.impacts_on_bathing_water,
            possible_pollutions=record.possible_pollutions,
            infrastructure=record.infrastructure or [],
            water_quality=record.water_quality,
            water_quality_from_year=record.water_quality_from_year,
            water_quality_to_year=record.water_quality_to_year,
            seasonal_status=record.seasonal_status,
            season_start=record.season_start,
            season_end=record.season_end,
            last_sample_date=record.last_sample_date,
            source_url=record.source_url,
            source_dataset=record.source_dataset,
            coordinates=SiteCoordinates(lat=record.lat, lon=record.lon),
        )

    @staticmethod
    def _unwrap_record(record: Any) -> Any:
        if hasattr(record, "_mapping"):
            return next(iter(record._mapping.values()))
        return record

    @staticmethod
    def _build_missing_bathing_image_url(
        item_id: str | None,
        item_type: str | None,
        district: str | None,
        image_url: str | None,
    ) -> str | None:
        if image_url or item_type != "badestelle" or not item_id:
            return image_url

        site_id = item_id.removeprefix("badestelle-")
        return build_bathing_image_url(site_id, district)

    @staticmethod
    def _row_to_map_item(row: dict[str, Any]) -> MapItem:
        return MapItem(
            id=row["id"],
            slug=row["slug"],
            type=row["type"],
            title=row["title"],
            description=row["description"],
            category=row["category"],
            lat=row["lat"],
            lng=row["lng"],
            address=row["address"],
            postcode=row["postcode"],
            city=row["city"],
            municipality=row.get("municipality"),
            image_url=PostgresStore._build_missing_bathing_image_url(
                row["id"],
                row["type"],
                row.get("district"),
                row["image_url"],
            ),
            website=row["website"],
            source_name=row.get("source_name"),
            content_license=row.get("content_license"),
            tags=row["tags"] or [],
            water_quality=row["water_quality"],
            accessibility=row["accessibility"],
            possible_pollutions=row["possible_pollutions"],
            seasonal_status=row["seasonal_status"],
            season_start=row["season_start"],
            season_end=row["season_end"],
            last_update=row["last_update"],
            district=row["district"],
            opening_hours=row["opening_hours"],
            amenities=row["amenities"] or [],
            distance_km=row.get("distance_km"),
        )

    @staticmethod
    def _record_to_map_item(record: MapItemRecord) -> MapItem:
        return MapItem(
            id=record.id,
            slug=record.slug,
            type=record.type,  # type: ignore[arg-type]
            title=record.title,
            description=record.description,
            category=record.category,
            lat=record.lat,
            lng=record.lng,
            address=record.address,
            postcode=record.postcode,
            city=record.city,
            municipality=record.municipality,
            image_url=PostgresStore._build_missing_bathing_image_url(
                record.id,
                record.type,
                record.district,
                record.image_url,
            ),
            website=record.website,
            source_name=record.source_name,
            content_license=record.content_license,
            tags=record.tags or [],
            water_quality=record.water_quality,
            accessibility=record.accessibility,
            possible_pollutions=record.possible_pollutions,
            seasonal_status=record.seasonal_status,
            season_start=record.season_start,
            season_end=record.season_end,
            last_update=record.last_update,
            district=record.district,
            opening_hours=record.opening_hours,
            amenities=record.amenities or [],
        )

    @staticmethod
    def _to_bathing_map_items(items: list[BathingSite], data_updated_at: datetime) -> list[MapItem]:
        mapped: list[MapItem] = []
        for site in items:
            last_update = datetime.combine(site.last_sample_date, datetime.min.time(
            )) if site.last_sample_date else data_updated_at
            description = site.bathing_spot_information or site.description or site.impacts_on_bathing_water
            category = site.bathing_water_type or site.water_category or "Badestelle"
            city = site.municipality or site.district
            address = ", ".join(
                part for part in [site.municipality, site.district] if part) or None
            tags = sorted({tag for tag in [
                          *site.infrastructure, site.water_category, site.coastal_water, site.region] if tag})
            title = site.common_name or site.short_name or site.name
            mapped.append(
                MapItem(
                    id=f"badestelle-{site.id}",
                    slug=PostgresStore._slugify(
                        f"{title}-{site.municipality or site.district or ''}-{site.id}"),
                    type="badestelle",
                    title=title,
                    description=description,
                    category=category,
                    lat=site.coordinates.lat,
                    lng=site.coordinates.lon,
                    address=address,
                    city=city,
                    municipality=site.municipality,
                    image_url=build_bathing_image_url(site.id, site.district),
                    website=site.source_url,
                    tags=tags,
                    water_quality=site.water_quality,
                    accessibility=None,
                    possible_pollutions=site.possible_pollutions,
                    seasonal_status=site.seasonal_status,
                    season_start=site.season_start,
                    season_end=site.season_end,
                    last_update=last_update,
                    district=site.district,
                    amenities=site.infrastructure,
                )
            )
        return mapped

    @staticmethod
    def _slugify(value: str) -> str:
        import re

        normalized = (
            value.casefold()
            .replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ß", "ss")
        )
        slug = re.sub(r"[^a-z0-9]+", "-", normalized)
        return slug.strip("-")

    @staticmethod
    def _to_feature_collection(visible_items: list[MapItem], all_items: list[MapItem]) -> MapFeatureCollection:
        return MapFeatureCollection(
            features=[
                MapFeature(
                    id=item.id,
                    geometry=MapPointGeometry(
                        coordinates=(item.lng, item.lat)),
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
            ],
            filters=MapFilters(
                types=sorted({item.type for item in all_items}),
                categories=sorted(
                    {item.category for item in all_items if item.category}),
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
            total=len(visible_items),
        )
