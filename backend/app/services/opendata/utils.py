import math
import re
from urllib.parse import quote
from datetime import date, datetime

from pyproj import Transformer

DISTRICT_LICENSE_CODES: dict[str, str] = {
    "Dithmarschen": "HEI",
    "Flensburg, Stadt": "FL",
    "Herzogtum Lauenburg": "RZ",
    "Kiel, Landeshauptstadt": "KI",
    "Lübeck, Hansestadt": "HL",
    "Neumünster, Stadt": "NMS",
    "Nordfriesland": "NF",
    "Ostholstein": "OH",
    "Pinneberg": "PI",
    "Plön": "PLÖ",
    "Rendsburg-Eckernförde": "RD",
    "Schleswig-Flensburg": "SL",
    "Segeberg": "SE",
    "Steinburg": "IZ",
    "Stormarn": "OD",
}

_UTM32_TO_WGS84 = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def normalize_bathing_coordinates(
    utm_east: float | None,
    utm_north: float | None,
    lon: float | None,
    lat: float | None,
) -> tuple[float | None, float | None]:
    if utm_east is not None and utm_north is not None:
        normalized_lon, normalized_lat = _UTM32_TO_WGS84.transform(utm_east, utm_north)
        return normalized_lon, normalized_lat
    return lon, lat


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        parsed_date = parse_date(value)
        if parsed_date is None:
            return None
        return datetime.combine(parsed_date, datetime.min.time())


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\r", " ").replace("\xa0", " ")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = text.strip(" ,;\n")
    return text or None


def as_sorted_values(values: list[str | None]) -> list[str]:
    return sorted({value for value in values if value})


def district_license_code(value: str | None) -> str | None:
    if not value:
        return None
    return DISTRICT_LICENSE_CODES.get(value)


def build_bathing_image_url(site_id: str | None, district: str | None) -> str | None:
    if not site_id:
        return None

    district_code = district_license_code(district)
    if not district_code:
        return None

    match = re.search(r"(\d{4})$", site_id)
    if not match:
        return None

    return (
        "https://efi2.schleswig-holstein.de/bg/files/Fotos/"
        f"Fotos_{quote(district_code)}/{match.group(1)}_Foto_Internet.JPG"
    )


def slugify(value: str) -> str:
    normalized = (
        value.casefold()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", normalized)
    return slug.strip("-")


def title_case_preserving_separators(value: str) -> str:
    return re.sub(
        r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'/-]*",
        lambda match: match.group(0).capitalize(),
        value.casefold(),
    )


def normalize_bathing_title(value: str) -> str:
    normalized = title_case_preserving_separators(value)
    normalized = normalized.replace("St. Peter-ording", "St. Peterording")
    return normalized


def split_bathing_name_parts(value: str | None) -> list[str]:
    cleaned = clean_text(value)
    if not cleaned:
        return []
    return [part.strip() for part in cleaned.split(";") if part.strip()]


def normalize_bathing_region(value: str | None) -> str | None:
    if not value:
        return None
    mapping = {
        "nords": "Nordsee",
        "osts": "Ostsee",
    }
    return mapping.get(value.casefold())


def canonical_slug_tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    normalized = value.casefold()
    normalized = normalized.replace("st.", "sankt")
    normalized = normalized.replace("st ", "sankt ")
    normalized = normalized.replace("peter-ording", "peter ording")
    normalized = normalized.replace("peterording", "peter ording")
    slug = slugify(normalized)
    return {part for part in slug.split("-") if part}


def is_redundant_slug_part(base: str, candidate: str) -> bool:
    candidate_tokens = canonical_slug_tokens(candidate)
    if not candidate_tokens:
        return True
    base_tokens = canonical_slug_tokens(base)
    return candidate_tokens.issubset(base_tokens)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))
