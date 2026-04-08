from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_PUBLIC_DIR = ROOT / "frontend" / "public"
OUTPUT_PATH = FRONTEND_PUBLIC_DIR / "sitemap.xml"

sys.path.insert(0, str(BACKEND_DIR))

from app.services.opendata import OpenDataService  # noqa: E402


@dataclass(frozen=True)
class SitemapUrl:
    loc: str
    lastmod: str
    changefreq: str
    priority: str


def read_env_value(key: str) -> str | None:
    value = os.environ.get(key)
    if value:
        return value

    env_path = ROOT / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        env_key, env_value = line.split("=", 1)
        if env_key.strip() != key:
            continue
        cleaned = env_value.strip().strip("'").strip('"')
        return cleaned or None

    return None


def normalize_site_url(raw: str | None) -> str:
    if not raw:
        raise RuntimeError("NUXT_PUBLIC_SITE_URL is missing in environment or .env")
    return raw.rstrip("/")


def iso_date(value: datetime | None = None) -> str:
    target = value or datetime.now(timezone.utc)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    return target.date().isoformat()


def build_xml(urls: list[SitemapUrl]) -> str:
    entries = []
    for url in urls:
        entries.append(
            "  <url>\n"
            f"    <loc>{escape(url.loc)}</loc>\n"
            f"    <lastmod>{url.lastmod}</lastmod>\n"
            f"    <changefreq>{url.changefreq}</changefreq>\n"
            f"    <priority>{url.priority}</priority>\n"
            "  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{chr(10).join(entries)}\n"
        "</urlset>\n"
    )


async def collect_urls() -> list[SitemapUrl]:
    site_url = normalize_site_url(read_env_value("NUXT_PUBLIC_SITE_URL"))
    service = OpenDataService()
    items = await service._get_map_items()
    generated_at = iso_date()

    urls: dict[str, SitemapUrl] = {
        f"{site_url}/": SitemapUrl(
            loc=f"{site_url}/",
            lastmod=generated_at,
            changefreq="daily",
            priority="1.0",
        ),
        f"{site_url}/impressum": SitemapUrl(
            loc=f"{site_url}/impressum",
            lastmod=generated_at,
            changefreq="yearly",
            priority="0.2",
        ),
        f"{site_url}/datenschutz": SitemapUrl(
            loc=f"{site_url}/datenschutz",
            lastmod=generated_at,
            changefreq="yearly",
            priority="0.2",
        ),
    }

    for item in items:
        slug = quote(item.slug, safe="-")
        lastmod = iso_date(item.last_update)
        loc = f"{site_url}/{slug}"
        urls[loc] = SitemapUrl(
            loc=loc,
            lastmod=lastmod,
            changefreq="weekly",
            priority="0.8" if item.type == "badestelle" else "0.6",
        )

    return [urls[key] for key in sorted(urls)]


async def main() -> None:
    urls = await collect_urls()
    FRONTEND_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_xml(urls), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} with {len(urls)} URLs")


if __name__ == "__main__":
    asyncio.run(main())
