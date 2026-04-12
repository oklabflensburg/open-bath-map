from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.map_item import (
    MapFeatureCollection, MapItem, MapItemSearchResponse
)
from app.services.opendata import OpenDataService

router = APIRouter(prefix="/api/map/v1", tags=["map"])


def get_service() -> OpenDataService:
    return OpenDataService()


@router.get("/bounds", response_model=MapFeatureCollection)
async def get_items_by_bounds(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    item_type: str | None = Query(default=None, alias="type"),
    category: str | None = None,
    infrastructure: str | None = None,
    service: OpenDataService = Depends(get_service),
) -> MapFeatureCollection:
    return await service.get_map_items_by_bounds(
        xmin=xmin,
        ymin=ymin,
        xmax=xmax,
        ymax=ymax,
        item_type=item_type,
        category=category,
        infrastructure=infrastructure,
    )


@router.get("/radius", response_model=MapFeatureCollection)
async def get_items_by_radius(
    lat: float,
    lng: float,
    radius_km: float | None = Query(default=25, ge=0),
    item_type: str | None = Query(default=None, alias="type"),
    category: str | None = None,
    infrastructure: str | None = None,
    service: OpenDataService = Depends(get_service),
) -> MapFeatureCollection:
    return await service.get_map_items_by_radius(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        item_type=item_type,
        category=category,
        infrastructure=infrastructure,
    )


@router.get("/details", response_model=MapItem)
async def get_item_details(
    id: str | None = None,
    slug: str | None = None,
    service: OpenDataService = Depends(get_service),
) -> MapItem:
    item = await service.get_map_item_details(item_id=id, slug=slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Map item not found")
    return item


@router.get("/search", response_model=MapItemSearchResponse)
async def search_items(
    q: str = Query(min_length=2),
    item_type: str | None = Query(default=None, alias="type"),
    category: str | None = None,
    infrastructure: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    service: OpenDataService = Depends(get_service),
) -> MapItemSearchResponse:
    return await service.search_map_items(
        q=q,
        item_type=item_type,
        category=category,
        infrastructure=infrastructure,
        limit=limit,
    )


@router.get("/items", response_model=MapItemSearchResponse)
async def list_items(
    item_type: str | None = Query(default=None, alias="type"),
    category: str | None = None,
    infrastructure: str | None = None,
    limit: int = Query(default=5000, ge=1, le=10000),
    service: OpenDataService = Depends(get_service),
) -> MapItemSearchResponse:
    return await service.list_map_items(
        item_type=item_type,
        category=category,
        infrastructure=infrastructure,
        limit=limit,
    )
