from dataclasses import dataclass
from datetime import datetime

from app.models.bathing_site import BathingSite
from app.models.map_item import MapItem


@dataclass
class CachedDataset:
    items: list[BathingSite]
    poi_items: list[MapItem]
    data_updated_at: datetime
    source_urls: dict[str, str]
    cached_at: datetime
