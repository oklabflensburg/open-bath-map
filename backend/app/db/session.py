from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine, async_sessionmaker, create_async_engine
)
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import Settings, get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_database_url(settings: Settings | None = None) -> str | None:
    active_settings = settings or get_settings()
    database_url = active_settings.database_url
    if not database_url:
        return None
    if database_url.startswith("postgresql+"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
    return database_url


def _get_engine(settings: Settings | None = None) -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        database_url = get_database_url(settings)
        if not database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        _engine = create_async_engine(database_url, future=True)
        _sessionmaker = async_sessionmaker(
            _engine, expire_on_commit=False, class_=AsyncSession)
    return _engine


def create_session(settings: Settings | None = None) -> AsyncSession:
    global _sessionmaker
    if _sessionmaker is None:
        _get_engine(settings)
    assert _sessionmaker is not None
    return _sessionmaker()


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


async def ensure_database_support_objects(
    settings: Settings | None = None
) -> None:
    engine = _get_engine(settings)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION immutable_unaccent(TEXT)
                RETURNS TEXT
                LANGUAGE sql
                IMMUTABLE
                PARALLEL SAFE
                AS $$
                    SELECT public.unaccent($1)
                $$;
                """
            )
        )


@asynccontextmanager
async def session_scope(settings: Settings | None = None):
    session = create_session(settings)
    try:
        yield session
    finally:
        await session.close()
