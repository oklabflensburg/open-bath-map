from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from collections.abc import Callable

import httpx

from app.config import Settings, get_settings
from app.models.map_item import MapItem

from .utils import clean_text, slugify

WIKIPEDIA_API_URL = "https://de.wikipedia.org/w/api.php"
USER_AGENT = "OpenBathMap/0.1 (https://github.com/oklabflensburg/open-bath-map)"
CACHE_VERSION = 1


class WikiEnricher:
    _cache: dict[str, dict[str, Any]] | None = None

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.cache_path = Path(self.settings.cache_dir) / "wiki-cache.json"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    async def enrich_item(self, item: MapItem) -> MapItem:
        cached = self._cache_entry(item.id)
        if cached is not None:
            return item.model_copy(update=self._cache_to_update(cached))

        enrichment = await self._fetch_enrichment(item)
        self._store_cache_entry(item.id, enrichment or {"matched": False})
        if enrichment is None:
            return item
        return item.model_copy(update=enrichment)

    async def enrich_items(self, items: list[MapItem]) -> list[MapItem]:
        return await self.enrich_items_with_progress(items)

    async def enrich_items_with_progress(
        self,
        items: list[MapItem],
        progress: Callable[[str], None] | None = None,
        label: str | None = None,
    ) -> list[MapItem]:
        if not items:
            if progress and label:
                progress(f"{label}: keine Einträge zu prüfen")
            return []

        enriched: list[MapItem] = []
        label_prefix = f"{label}: " if label else ""
        cache_hits = 0
        fetched = 0
        matched = 0
        unmatched = 0

        if progress:
            progress(f"{label_prefix}0/{len(items)} verarbeitet")

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            for index, item in enumerate(items, start=1):
                cached = self._cache_entry(item.id)
                if cached is not None:
                    cache_hits += 1
                    if cached.get("matched"):
                        matched += 1
                    else:
                        unmatched += 1
                    enriched.append(item.model_copy(update=self._cache_to_update(cached)))
                else:
                    fetched += 1
                    enrichment = await self._fetch_enrichment(item, client=client)
                    self._store_cache_entry(item.id, enrichment or {"matched": False})
                    if enrichment is None:
                        unmatched += 1
                        enriched.append(item)
                    else:
                        matched += 1
                        if progress:
                            links = [
                                value
                                for value in [
                                    enrichment.get("wikipedia_url"),
                                    enrichment.get("wikidata_url"),
                                ]
                                if isinstance(value, str) and value
                            ]
                            joined_links = " | ".join(links) if links else "keine externen Links"
                            progress(f"{label_prefix}Treffer für {item.id} ({item.title}): {joined_links}")
                        enriched.append(item.model_copy(update=enrichment))

                if progress and (index == len(items) or index == 1 or index % 50 == 0):
                    progress(
                        f"{label_prefix}{index}/{len(items)} verarbeitet "
                        f"(Cache: {cache_hits}, neu: {fetched}, Treffer: {matched}, ohne Treffer: {unmatched})",
                    )

        return enriched

    def _cache_entry(self, item_id: str) -> dict[str, Any] | None:
        cache = self._load_cache()
        entry = cache.get(item_id)
        if not isinstance(entry, dict):
            return None
        if entry.get("cache_version") != CACHE_VERSION:
            return None
        return entry

    def _store_cache_entry(self, item_id: str, value: dict[str, Any]) -> None:
        cache = self._load_cache()
        cache[item_id] = {"cache_version": CACHE_VERSION, **value}
        self.cache_path.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        if WikiEnricher._cache is not None:
            return WikiEnricher._cache

        if not self.cache_path.exists():
            WikiEnricher._cache = {}
            return WikiEnricher._cache

        try:
            loaded = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            loaded = {}

        WikiEnricher._cache = loaded if isinstance(loaded, dict) else {}
        return WikiEnricher._cache

    @staticmethod
    def _cache_to_update(value: dict[str, Any]) -> dict[str, Any]:
        if not value.get("matched"):
            return {}
        return {
            key: value.get(key)
            for key in [
                "wikipedia_url",
                "wikipedia_title",
                "wikipedia_summary",
                "wikidata_id",
                "wikidata_url",
            ]
        }

    @staticmethod
    def _clean_summary(value: str | None) -> str | None:
        summary = clean_text(value)
        if not summary:
            return None
        summary = re.sub(r"\b(?:[a-z]\d+){2,}\b", " ", summary)
        summary = re.sub(r"\s+", " ", summary).strip()
        return summary or None

    async def _fetch_enrichment(
        self,
        item: MapItem,
        client: httpx.AsyncClient | None = None,
    ) -> dict[str, Any] | None:
        if client is not None:
            best_title = await self._find_best_title(client, item)
            if not best_title:
                return None
            return await self._fetch_page_details(client, best_title)

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as local_client:
            best_title = await self._find_best_title(local_client, item)
            if not best_title:
                return None
            return await self._fetch_page_details(local_client, best_title)

    async def _find_best_title(self, client: httpx.AsyncClient, item: MapItem) -> str | None:
        candidates = await self._search_candidates(client, item)
        if item.type == "poi":
            candidates.extend(await self._geosearch_candidates(client, item))

        best_title: str | None = None
        best_score = 0.0
        seen_titles: set[str] = set()

        for candidate in candidates:
            title = clean_text(str(candidate.get("title") or ""))
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            score = self._candidate_score(item, candidate)
            if score > best_score:
                best_score = score
                best_title = title

        if best_score < 7.5:
            return None
        return best_title

    async def _search_candidates(self, client: httpx.AsyncClient, item: MapItem) -> list[dict[str, Any]]:
        queries = [item.title]
        if item.city and item.city.casefold() not in item.title.casefold():
            queries.append(f"{item.title} {item.city}")
        elif item.district and item.district.casefold() not in item.title.casefold():
            queries.append(f"{item.title} {item.district}")

        results: list[dict[str, Any]] = []
        for query in queries:
            response = await client.get(
                WIKIPEDIA_API_URL,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": 5,
                    "format": "json",
                },
            )
            response.raise_for_status()
            payload = response.json()
            search_results = payload.get("query", {}).get("search", [])
            if isinstance(search_results, list):
                results.extend(search_results)
        return results

    async def _geosearch_candidates(self, client: httpx.AsyncClient, item: MapItem) -> list[dict[str, Any]]:
        response = await client.get(
            WIKIPEDIA_API_URL,
            params={
                "action": "query",
                "list": "geosearch",
                "gscoord": f"{item.lat}|{item.lng}",
                "gsradius": 10000,
                "gslimit": 10,
                "format": "json",
            },
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("query", {}).get("geosearch", [])
        return results if isinstance(results, list) else []

    def _candidate_score(self, item: MapItem, candidate: dict[str, Any]) -> float:
        item_slug = slugify(item.title)
        title = clean_text(str(candidate.get("title") or "")) or ""
        title_slug = slugify(title)
        item_tokens = {part for part in item_slug.split("-") if part}
        title_tokens = {part for part in title_slug.split("-") if part}
        if not item_tokens or not title_tokens:
            return 0.0

        overlap = item_tokens & title_tokens
        overlap_ratio = len(overlap) / max(1, len(item_tokens))
        score = overlap_ratio * 10

        if item_slug == title_slug:
            score += 8
        elif title_slug.startswith(item_slug) or item_slug.startswith(title_slug):
            score += 4

        snippet = clean_text(str(candidate.get("snippet") or "")) or ""
        context = " ".join(part for part in [item.city, item.district, item.category] if part).casefold()
        if context and any(part in snippet.casefold() for part in context.split() if len(part) >= 4):
            score += 1.5

        distance = candidate.get("dist")
        if isinstance(distance, (int, float)):
            score += max(0.0, 2 - (float(distance) / 5000))

        return score

    async def _fetch_page_details(self, client: httpx.AsyncClient, title: str) -> dict[str, Any] | None:
        response = await client.get(
            WIKIPEDIA_API_URL,
            params={
                "action": "query",
                "prop": "pageprops|info|extracts",
                "inprop": "url",
                "ppprop": "wikibase_item",
                "exintro": 1,
                "explaintext": 1,
                "exchars": 600,
                "redirects": 1,
                "titles": title,
                "format": "json",
            },
        )
        response.raise_for_status()
        payload = response.json()
        pages = payload.get("query", {}).get("pages", {})
        if not isinstance(pages, dict):
            return None

        page = next(iter(pages.values()), None)
        if not isinstance(page, dict) or "missing" in page:
            return None

        wikipedia_url = clean_text(page.get("fullurl"))
        wikipedia_title = clean_text(page.get("title"))
        wikipedia_summary = self._clean_summary(page.get("extract"))
        wikidata_id = clean_text((page.get("pageprops") or {}).get("wikibase_item"))

        return {
            "matched": True,
            "wikipedia_url": wikipedia_url,
            "wikipedia_title": wikipedia_title,
            "wikipedia_summary": wikipedia_summary,
            "wikidata_id": wikidata_id,
            "wikidata_url": f"https://www.wikidata.org/wiki/{wikidata_id}" if wikidata_id else None,
        }
