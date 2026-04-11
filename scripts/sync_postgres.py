from __future__ import annotations

import asyncio
from datetime import datetime
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.opendata import OpenDataService  # noqa: E402


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


async def main() -> None:
    service = OpenDataService()
    log("Starte PostgreSQL-Sync")
    result = await service.sync_database(progress=log)
    log(
        f"Fertig: {result['bathing_sites']} Badestellen und {result['poi_items']} POIs synchronisiert.",
    )


if __name__ == "__main__":
    asyncio.run(main())
