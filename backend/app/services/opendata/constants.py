CKAN_API_URL = "https://opendata.schleswig-holstein.de/api/3/action/package_search"

SOURCE_QUERIES = {
    "stammdaten": {
        "term": "badegewasser stammdaten",
        "title": "Badegewässer Stammdaten",
        "preferred_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_badegewaesser_odata.csv",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_badegewaesser_odata.csv",
    },
    "einstufung": {
        "term": "badegewasser einstufung",
        "title": "Badegewässer Einstufung",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_einstufung_odata.csv",
    },
    "infrastruktur": {
        "term": "badegewasser infrastruktur",
        "title": "Badegewässer Infrastruktur",
        "preferred_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_infrastruktur_odata.csv",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_infrastruktur_odata.csv",
    },
    "saison": {
        "term": "badegewasser saisondauer",
        "title": "Badegewässer Saisondauer",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_badesaison_odata.csv",
    },
    "messungen": {
        "term": "badegewasser messungen",
        "title": "Badegewässer Messungen",
        "preferred_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_proben_odata.csv",
        "fallback_url": "http://efi2.schleswig-holstein.de/bg/opendata/v_proben_odata.csv",
    },
}

STAMMDATEN_COLUMNS = [
    "bathing_water_id",
    "bathing_water_name",
    "short_name",
    "common_name",
    "water_category",
    "coastal_water",
    "bathing_water_type",
    "description",
    "bathing_spot_length_m",
    "eu_registration",
    "eu_deregistration",
    "river_basin_district_id",
    "river_basin_district_name",
    "water_body_id",
    "water_body_name",
    "natural_water_body_id",
    "natural_water_body_name",
    "keywords",
    "district_number",
    "district",
    "municipality_number",
    "municipality",
    "utm_east",
    "utm_north",
    "lon",
    "lat",
    "bathing_spot_information",
    "impacts_on_bathing_water",
    "possible_pollutions",
]

EINSTUFUNG_COLUMNS = ["bathing_water_id", "from_year", "to_year", "water_quality"]
INFRASTRUCTURE_COLUMNS = ["bathing_water_id", "infrastructure_id", "infrastructure_label"]
SAISON_COLUMNS = ["bathing_water_id", "season_start", "season_end", "seasonal_status"]
MEASUREMENT_COLUMNS = [
    "bathing_water_id",
    "bathing_water_name",
    "sampling_point",
    "water_depth_cm",
    "monitoring_reason",
    "water_category",
    "coastal_water",
    "measurement_id",
    "sample_date",
    "sample_type",
    "intestinal_enterococci",
    "e_coli",
    "water_temperature_c",
    "air_temperature_c",
    "transparency_m",
]

POI_SOURCE_QUERY = {
    "term": "POI der Touristischen Landesdatenbank",
    "title": "POI der Touristischen Landesdatenbank",
}

POI_INCLUDE_KEYWORDS = [
    "badestelle",
    "naturbad",
    "strand",
    "strandpromenade",
    "promenade",
    "seebrücke",
    "seebruecke",
    "ufer",
    "hafen",
    "förde",
    "foerde",
    "meer",
    "küste",
    "kueste",
    "kanal",
    "see",
    "wassersport",
    "marina",
    "anleger",
    "schiff",
    "aussichtspunkt",
]

POI_EXCLUDE_KEYWORDS = [
    "hotel",
    "restaurant",
    "café",
    "cafe",
    "bar",
    "ferienwohnung",
    "ferienhaus",
    "ferienpark",
    "camping",
    "wohnmobil",
    "parkplatz",
    "golf",
    "museum",
    "unterkunft",
]
