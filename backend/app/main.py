from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.bathing_sites import router as bathing_sites_router
from app.api.routes.health import router as health_router
from app.api.routes.map import router as map_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API für Badestellen in Schleswig-Holstein auf Basis offener Landesdaten.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(bathing_sites_router)
app.include_router(map_router)
