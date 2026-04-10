from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Open Bath Map API"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    backend_cors_origins: str = "http://127.0.0.1:3000,http://localhost:3000"
    cache_ttl_minutes: int = 360
    request_timeout_seconds: int = 30
    cache_dir: Path = Path("cache")
    database_url: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
