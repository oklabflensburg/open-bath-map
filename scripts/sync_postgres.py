from __future__ import annotations

import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.opendata import OpenDataService  # noqa: E402


async def main() -> None:
    service = OpenDataService()
    result = await service.sync_database()
    print(
        f"Synced PostgreSQL with {result['bathing_sites']} bathing sites and {result['poi_items']} POIs.",
    )


if __name__ == "__main__":
    asyncio.run(main())
