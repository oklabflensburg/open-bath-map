from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.bathing_site import BathingSite, BathingSiteListResponse
from app.services.opendata import OpenDataService

router = APIRouter(prefix="/api/bathing-sites", tags=["bathing-sites"])


def get_service() -> OpenDataService:
    return OpenDataService()


@router.get("", response_model=BathingSiteListResponse)
async def list_bathing_sites(
    q: str | None = Query(default=None, description="Name, Ort oder Region"),
    district: str | None = None,
    municipality: str | None = None,
    water_category: str | None = None,
    bathing_water_type: str | None = None,
    water_quality: str | None = None,
    infrastructure: str | None = None,
    bbox: str | None = Query(default=None, description="west,south,east,north"),
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float | None = Query(default=None, ge=0),
    service: OpenDataService = Depends(get_service),
) -> BathingSiteListResponse:
    return await service.list_sites(
        q=q,
        district=district,
        municipality=municipality,
        water_category=water_category,
        bathing_water_type=bathing_water_type,
        water_quality=water_quality,
        infrastructure=infrastructure,
        bbox=bbox,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
    )


@router.get("/{site_id}", response_model=BathingSite)
async def get_bathing_site(site_id: str, service: OpenDataService = Depends(get_service)) -> BathingSite:
    site = await service.get_site(site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Bathing site not found")
    return site
