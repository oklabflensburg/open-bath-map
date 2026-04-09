from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Awaitable, Callable

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from app.config import Settings, get_settings
from app.models.bathing_site import BathingSite, BathingSiteListResponse, FilterOptions, SiteCoordinates
from app.models.map_item import MapFeature, MapFeatureCollection, MapFeatureProperties, MapFilters, MapItem, MapItemSearchResponse, MapPointGeometry


class PostgresStore:
    _pool: AsyncConnectionPool | None = None
    _initialized = False

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def is_enabled(self) -> bool:
        return bool(self.settings.database_url)

    async def connect(self) -> None:
        if not self.is_enabled:
            return
        if PostgresStore._pool is None:
            PostgresStore._pool = AsyncConnectionPool(
                conninfo=self.settings.database_url,
                min_size=1,
                max_size=4,
                open=False,
            )
            await PostgresStore._pool.open()
            await PostgresStore._pool.wait()
        if not PostgresStore._initialized:
            await self._init_schema()
            PostgresStore._initialized = True

    async def close(self) -> None:
        if PostgresStore._pool is not None:
            await PostgresStore._pool.close()
            PostgresStore._pool = None
            PostgresStore._initialized = False

    async def ensure_seeded(self, loader: Callable[[], Awaitable[Any]]) -> None:
        if not self.is_enabled:
            return
        await self.connect()
        state = await self._fetch_one("SELECT synced_at FROM dataset_state WHERE id = 1")
        if state is not None:
            return
        await loader()

    async def save_dataset(self, dataset: Any, bathing_map_items: list[MapItem] | None = None) -> None:
        await self.connect()
        assert PostgresStore._pool is not None
        if bathing_map_items is None:
            bathing_map_items = self._to_bathing_map_items(dataset.items, dataset.data_updated_at)
        async with PostgresStore._pool.connection() as conn:
            async with conn.transaction():
                async with conn.cursor() as cur:
                    await cur.execute("DELETE FROM bathing_sites")
                    await cur.execute("DELETE FROM map_items")
                    await cur.executemany(
                        """
                        INSERT INTO bathing_sites (
                            id, name, short_name, common_name, municipality, district, region,
                            water_category, coastal_water, bathing_water_type, bathing_spot_length_m,
                            description, bathing_spot_information, impacts_on_bathing_water,
                            possible_pollutions, infrastructure, water_quality, water_quality_from_year,
                            water_quality_to_year, seasonal_status, season_start, season_end,
                            last_sample_date, source_url, source_dataset, search_text, lat, lon
                        ) VALUES (
                            %(id)s, %(name)s, %(short_name)s, %(common_name)s, %(municipality)s, %(district)s, %(region)s,
                            %(water_category)s, %(coastal_water)s, %(bathing_water_type)s, %(bathing_spot_length_m)s,
                            %(description)s, %(bathing_spot_information)s, %(impacts_on_bathing_water)s,
                            %(possible_pollutions)s, %(infrastructure)s, %(water_quality)s, %(water_quality_from_year)s,
                            %(water_quality_to_year)s, %(seasonal_status)s, %(season_start)s, %(season_end)s,
                            %(last_sample_date)s, %(source_url)s, %(source_dataset)s, %(search_text)s, %(lat)s, %(lon)s
                        )
                        """,
                        [self._bathing_site_params(item) for item in dataset.items],
                    )
                    await cur.executemany(
                        """
                    INSERT INTO map_items (
                        id, slug, type, title, description, category, lat, lng, address, postcode,
                        city, image_url, website, source_name, content_license, tags, water_quality, accessibility,
                        possible_pollutions, seasonal_status, season_start, season_end,
                        last_update, district, opening_hours, amenities, search_text
                    ) VALUES (
                        %(id)s, %(slug)s, %(type)s, %(title)s, %(description)s, %(category)s, %(lat)s, %(lng)s, %(address)s, %(postcode)s,
                        %(city)s, %(image_url)s, %(website)s, %(source_name)s, %(content_license)s, %(tags)s, %(water_quality)s, %(accessibility)s,
                        %(possible_pollutions)s, %(seasonal_status)s, %(season_start)s, %(season_end)s,
                        %(last_update)s, %(district)s, %(opening_hours)s, %(amenities)s, %(search_text)s
                    )
                        """,
                        [self._map_item_params(item) for item in [*dataset.poi_items, *bathing_map_items]],
                    )
                    await cur.execute(
                        """
                        INSERT INTO dataset_state (id, data_updated_at, synced_at, source_urls)
                        VALUES (1, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE
                        SET data_updated_at = EXCLUDED.data_updated_at,
                            synced_at = EXCLUDED.synced_at,
                            source_urls = EXCLUDED.source_urls
                        """,
                        (
                            dataset.data_updated_at,
                            dataset.cached_at,
                            Jsonb(dataset.source_urls),
                        ),
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
        where: list[str] = []
        select_params: list[Any] = []
        where_params: list[Any] = []
        order_params: list[Any] = []
        select_distance = ""
        select_rank = ""
        order_by = "ORDER BY district NULLS LAST, municipality NULLS LAST, name"

        if q:
            where.append(f"{self._search_vector_sql()} @@ websearch_to_tsquery('german', %s)")
            where_params.append(q)
            select_rank = f", ts_rank({self._search_vector_sql()}, websearch_to_tsquery('german', %s)) AS search_rank"
            select_params.append(q)
            order_by = "ORDER BY search_rank DESC, name"
        if district:
            where.append("district = %s")
            where_params.append(district)
        if municipality:
            where.append("municipality = %s")
            where_params.append(municipality)
        if water_category:
            where.append("water_category = %s")
            where_params.append(water_category)
        if bathing_water_type:
            where.append("bathing_water_type = %s")
            where_params.append(bathing_water_type)
        if water_quality:
            where.append("water_quality = %s")
            where_params.append(water_quality)
        if infrastructure:
            where.append("%s = ANY(infrastructure)")
            where_params.append(infrastructure)
        if bbox:
            west, south, east, north = [float(part) for part in bbox.split(",")]
            where.append("lon BETWEEN %s AND %s")
            where_params.extend([west, east])
            where.append("lat BETWEEN %s AND %s")
            where_params.extend([south, north])
        if lat is not None and lon is not None:
            distance_sql = self._distance_sql()
            select_distance = f", {distance_sql} AS distance_km"
            select_params.extend(self._distance_params(lat, lon))
            if radius_km is not None:
                where.insert(0, f"{distance_sql} <= %s")
                where_params = [*self._distance_params(lat, lon), radius_km, *where_params]
            order_by = "ORDER BY distance_km NULLS LAST, name"

        rows = await self._fetch_all(
            f"""
            SELECT *, lat, lon {select_rank} {select_distance}
            FROM bathing_sites
            {self._where_clause(where)}
            {order_by}
            """,
            [*select_params, *where_params, *order_params],
        )
        filters = await self._build_filter_options()
        state = await self._get_dataset_state()
        items = [self._row_to_bathing_site(row) for row in rows]
        return BathingSiteListResponse(
            items=items,
            total=len(items),
            filter_options=filters,
            data_updated_at=state["data_updated_at"],
        )

    async def get_site(self, site_id: str) -> BathingSite | None:
        row = await self._fetch_one("SELECT * FROM bathing_sites WHERE id = %s", (site_id,))
        return self._row_to_bathing_site(row) if row else None

    async def health(self) -> dict[str, Any]:
        state = await self._get_dataset_state()
        item_count_row = await self._fetch_one(
            """
            SELECT
              (SELECT COUNT(*) FROM bathing_sites) + (SELECT COUNT(*) FROM map_items WHERE type = 'poi') AS item_count
            """
        )
        age = int((datetime.utcnow() - state["synced_at"].replace(tzinfo=None)).total_seconds())
        return {
            "status": "ok",
            "cache_age_seconds": age,
            "cached_at": state["synced_at"],
            "source_urls": state["source_urls"],
            "item_count": item_count_row["item_count"],
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
        rows = await self._fetch_all(
            f"""
            SELECT *, {self._distance_sql()} AS distance_km
            FROM map_items
            {self._where_clause(self._map_where(item_type, category, infrastructure) + ([f"{self._distance_sql()} <= %s"] if radius_km is not None else []))}
            ORDER BY distance_km NULLS LAST, title
            """,
            [
                *self._distance_params(lat, lng),
                *self._map_params(item_type, category, infrastructure),
                *([*self._distance_params(lat, lng), radius_km] if radius_km is not None else []),
            ],
        )
        visible_items = [self._row_to_map_item(row) for row in rows]
        all_items = await self._query_map_items(
            item_type=item_type,
            category=category,
            infrastructure=infrastructure,
        )
        return self._to_feature_collection(visible_items, all_items)

    async def get_map_item_details(self, *, item_id: str | None, slug: str | None) -> MapItem | None:
        if item_id:
            row = await self._fetch_one("SELECT * FROM map_items WHERE id = %s", (item_id,))
        elif slug:
            row = await self._fetch_one("SELECT * FROM map_items WHERE slug = %s", (slug,))
        else:
            row = None
        return self._row_to_map_item(row) if row else None

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
        base_where: list[str] = []
        params: list[Any] = []
        if item_type in {"badestelle", "poi"}:
            base_where.append("type = %s")
            params.append(item_type)
        if category:
            base_where.append("category = %s")
            params.append(category)
        if infrastructure:
            base_where.append("(%s = ANY(amenities) OR accessibility = %s)")
            params.extend([infrastructure, infrastructure])
        search_predicate = (
            f"{self._search_vector_sql()} @@ websearch_to_tsquery('german', %s) "
            f"OR {self._normalized_search_sql()} LIKE '%%' || %s || '%%' "
            f"OR {self._normalized_search_sql()} %% %s "
            f"OR word_similarity(%s, {self._normalized_search_sql()}) >= 0.5"
        )
        where = [*base_where, f"({search_predicate})"]
        rows = await self._fetch_all(
            f"""
            SELECT *,
                   ts_rank({self._search_vector_sql()}, websearch_to_tsquery('german', %s)) AS search_rank,
                   similarity({self._normalized_search_sql()}, %s) AS similarity_rank,
                   word_similarity(%s, {self._normalized_search_sql()}) AS word_similarity_rank
            FROM map_items
            {self._where_clause(where)}
            ORDER BY
                CASE WHEN {self._search_vector_sql()} @@ websearch_to_tsquery('german', %s) THEN 0 ELSE 1 END,
                GREATEST(
                    ts_rank({self._search_vector_sql()}, websearch_to_tsquery('german', %s)),
                    similarity({self._normalized_search_sql()}, %s),
                    word_similarity(%s, {self._normalized_search_sql()})
                ) DESC,
                title
            LIMIT %s
            """,
            [
                q,
                normalized_query,
                normalized_query,
                *params,
                q,
                normalized_query,
                normalized_query,
                q,
                q,
                normalized_query,
                normalized_query,
                q,
                limit,
            ],
        )
        total_row = await self._fetch_one(
            f"""
            SELECT COUNT(*) AS total
            FROM map_items
            {self._where_clause(where)}
            """,
            [*params, q, normalized_query, normalized_query, normalized_query],
        )
        items = [self._row_to_map_item(row) for row in rows]
        return MapItemSearchResponse(items=items, total=total_row["total"] if total_row else len(items))

    async def _query_map_items(
        self,
        *,
        item_type: str | None,
        category: str | None,
        infrastructure: str | None,
    ) -> list[MapItem]:
        rows = await self._fetch_all(
            f"""
            SELECT *
            FROM map_items
            {self._where_clause(self._map_where(item_type, category, infrastructure))}
            ORDER BY city NULLS LAST, category NULLS LAST, title
            """,
            self._map_params(item_type, category, infrastructure),
        )
        return [self._row_to_map_item(row) for row in rows]

    def _map_where(self, item_type: str | None, category: str | None, infrastructure: str | None) -> list[str]:
        where: list[str] = []
        if item_type in {"badestelle", "poi"}:
            where.append("type = %s")
        if category:
            where.append("category = %s")
        if infrastructure:
            where.append("(%s = ANY(amenities) OR accessibility = %s)")
        return where

    def _map_params(self, item_type: str | None, category: str | None, infrastructure: str | None) -> list[Any]:
        params: list[Any] = []
        if item_type in {"badestelle", "poi"}:
            params.append(item_type)
        if category:
            params.append(category)
        if infrastructure:
            params.extend([infrastructure, infrastructure])
        return params

    async def _build_filter_options(self) -> FilterOptions:
        row = await self._fetch_one(
            """
            SELECT
              ARRAY(SELECT DISTINCT district FROM bathing_sites WHERE district IS NOT NULL ORDER BY district) AS districts,
              ARRAY(SELECT DISTINCT municipality FROM bathing_sites WHERE municipality IS NOT NULL ORDER BY municipality) AS municipalities,
              ARRAY(SELECT DISTINCT water_category FROM bathing_sites WHERE water_category IS NOT NULL ORDER BY water_category) AS water_categories,
              ARRAY(SELECT DISTINCT coastal_water FROM bathing_sites WHERE coastal_water IS NOT NULL ORDER BY coastal_water) AS coastal_waters,
              ARRAY(SELECT DISTINCT bathing_water_type FROM bathing_sites WHERE bathing_water_type IS NOT NULL ORDER BY bathing_water_type) AS bathing_water_types,
              ARRAY(SELECT DISTINCT water_quality FROM bathing_sites WHERE water_quality IS NOT NULL ORDER BY water_quality) AS water_qualities,
              ARRAY(
                SELECT DISTINCT infrastructure
                FROM bathing_sites, unnest(infrastructure) AS infrastructure
                WHERE infrastructure IS NOT NULL
                ORDER BY infrastructure
              ) AS infrastructures
            """
        )
        return FilterOptions(**row)

    async def _get_dataset_state(self) -> dict[str, Any]:
        state = await self._fetch_one("SELECT * FROM dataset_state WHERE id = 1")
        if state is None:
            raise RuntimeError("PostgreSQL dataset is empty. Run the sync script or seed on first access.")
        return state

    async def _fetch_one(self, query: str, params: Any = ()) -> dict[str, Any] | None:
        await self.connect()
        assert PostgresStore._pool is not None
        async with PostgresStore._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def _fetch_all(self, query: str, params: Any = ()) -> list[dict[str, Any]]:
        await self.connect()
        assert PostgresStore._pool is not None
        async with PostgresStore._pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    async def _init_schema(self) -> None:
        statements = [
            "CREATE EXTENSION IF NOT EXISTS unaccent",
            "CREATE EXTENSION IF NOT EXISTS pg_trgm",
            """
            CREATE OR REPLACE FUNCTION immutable_unaccent(TEXT)
            RETURNS TEXT
            LANGUAGE sql
            IMMUTABLE
            PARALLEL SAFE
            AS $$
                SELECT public.unaccent($1)
            $$;
            """,
            """
            CREATE TABLE IF NOT EXISTS dataset_state (
              id SMALLINT PRIMARY KEY,
              data_updated_at TIMESTAMPTZ NOT NULL,
              synced_at TIMESTAMPTZ NOT NULL,
              source_urls JSONB NOT NULL DEFAULT '{}'::jsonb
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bathing_sites (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              short_name TEXT,
              common_name TEXT,
              municipality TEXT,
              district TEXT,
              region TEXT,
              water_category TEXT,
              coastal_water TEXT,
              bathing_water_type TEXT,
              bathing_spot_length_m DOUBLE PRECISION,
              description TEXT,
              bathing_spot_information TEXT,
              impacts_on_bathing_water TEXT,
              possible_pollutions TEXT,
              infrastructure TEXT[] NOT NULL DEFAULT '{}',
              water_quality TEXT,
              water_quality_from_year INTEGER,
              water_quality_to_year INTEGER,
              seasonal_status TEXT,
              season_start DATE,
              season_end DATE,
              last_sample_date DATE,
              source_url TEXT NOT NULL,
              source_dataset TEXT NOT NULL,
              search_text TEXT NOT NULL,
              lat DOUBLE PRECISION NOT NULL,
              lon DOUBLE PRECISION NOT NULL
            )
            """,
            f"CREATE INDEX IF NOT EXISTS idx_bathing_sites_search_german ON bathing_sites USING GIN ({self._search_vector_sql()})",
            f"CREATE INDEX IF NOT EXISTS idx_bathing_sites_search_trgm ON bathing_sites USING GIN ({self._normalized_search_sql()} gin_trgm_ops)",
            "CREATE INDEX IF NOT EXISTS idx_bathing_sites_coords ON bathing_sites (lat, lon)",
            """
            CREATE TABLE IF NOT EXISTS map_items (
              id TEXT PRIMARY KEY,
              slug TEXT NOT NULL UNIQUE,
              type TEXT NOT NULL,
              title TEXT NOT NULL,
              description TEXT,
              category TEXT,
              lat DOUBLE PRECISION NOT NULL,
              lng DOUBLE PRECISION NOT NULL,
              address TEXT,
              postcode TEXT,
              city TEXT,
              image_url TEXT,
              website TEXT,
              source_name TEXT,
              content_license TEXT,
              tags TEXT[] NOT NULL DEFAULT '{}',
              water_quality TEXT,
              accessibility TEXT,
              possible_pollutions TEXT,
              seasonal_status TEXT,
              season_start DATE,
              season_end DATE,
              last_update TIMESTAMPTZ,
              district TEXT,
              opening_hours TEXT,
              amenities TEXT[] NOT NULL DEFAULT '{}',
              search_text TEXT NOT NULL
            )
            """,
            "ALTER TABLE map_items ADD COLUMN IF NOT EXISTS source_name TEXT",
            "ALTER TABLE map_items ADD COLUMN IF NOT EXISTS content_license TEXT",
            f"CREATE INDEX IF NOT EXISTS idx_map_items_search_german ON map_items USING GIN ({self._search_vector_sql()})",
            f"CREATE INDEX IF NOT EXISTS idx_map_items_search_trgm ON map_items USING GIN ({self._normalized_search_sql()} gin_trgm_ops)",
            "CREATE INDEX IF NOT EXISTS idx_map_items_coords ON map_items (lat, lng)",
            "CREATE INDEX IF NOT EXISTS idx_map_items_type_category ON map_items (type, category)",
        ]
        assert PostgresStore._pool is not None
        async with PostgresStore._pool.connection() as conn:
            async with conn.transaction():
                for statement in statements:
                    await conn.execute(statement)

    @staticmethod
    def _where_clause(where: list[str]) -> str:
        return f"WHERE {' AND '.join(where)}" if where else ""

    @staticmethod
    def _distance_sql() -> str:
        return (
            "6371 * acos(least(1, greatest(-1, "
            "cos(radians(%s)) * cos(radians(lat)) * cos(radians(lng) - radians(%s)) + "
            "sin(radians(%s)) * sin(radians(lat))"
            ")))"
        )

    @staticmethod
    def _distance_params(lat: float, lng: float) -> list[float]:
        return [lat, lng, lat]

    @staticmethod
    def _search_vector_sql() -> str:
        return "to_tsvector('german', search_text)"

    @staticmethod
    def _normalized_search_sql() -> str:
        return "immutable_unaccent(lower(search_text))"

    @staticmethod
    def _normalize_search_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"\s+", " ", normalized.lower()).strip()
        return normalized

    @staticmethod
    def _bathing_site_params(item: BathingSite) -> dict[str, Any]:
        return {
            **item.model_dump(),
            "lat": item.coordinates.lat,
            "lon": item.coordinates.lon,
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
            "search_text": " ".join(
                filter(
                    None,
                    [
                        item.title,
                        item.description,
                        item.category,
                        item.address,
                        item.city,
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
            image_url=row["image_url"],
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
    def _to_bathing_map_items(items: list[BathingSite], data_updated_at: datetime) -> list[MapItem]:
        mapped: list[MapItem] = []
        for site in items:
            last_update = datetime.combine(site.last_sample_date, datetime.min.time()) if site.last_sample_date else data_updated_at
            description = site.bathing_spot_information or site.description or site.impacts_on_bathing_water
            category = site.bathing_water_type or site.water_category or "Badestelle"
            city = site.municipality or site.district
            address = ", ".join(part for part in [site.municipality, site.district] if part) or None
            tags = sorted({tag for tag in [*site.infrastructure, site.water_category, site.coastal_water, site.region] if tag})
            title = site.common_name or site.short_name or site.name
            mapped.append(
                MapItem(
                    id=f"badestelle-{site.id}",
                    slug=PostgresStore._slugify(f"{title}-{site.municipality or site.district or ''}-{site.id}"),
                    type="badestelle",
                    title=title,
                    description=description,
                    category=category,
                    lat=site.coordinates.lat,
                    lng=site.coordinates.lon,
                    address=address,
                    city=city,
                    image_url=None,
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
            ],
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
            total=len(visible_items),
        )
