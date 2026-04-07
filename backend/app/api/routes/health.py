from fastapi import APIRouter, Depends

from app.models.bathing_site import HealthResponse
from app.services.opendata import OpenDataService

router = APIRouter(prefix="/api", tags=["health"])


def get_service() -> OpenDataService:
    return OpenDataService()


@router.get("/health", response_model=HealthResponse)
async def health(service: OpenDataService = Depends(get_service)) -> HealthResponse:
    return HealthResponse.model_validate(await service.health())
