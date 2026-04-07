# Open Bath Map

Interaktive Open-Data-Kartenanwendung für Badestellen und wassernahe POIs in Schleswig-Holstein.

Die Lösung besteht aus:

- [frontend](/home/awendelk/git/open-bath-map/frontend): Nuxt 3, TypeScript, Tailwind CSS, Leaflet
- [backend](/home/awendelk/git/open-bath-map/backend): FastAPI, Python 3.12+, Pydantic, httpx

Das Frontend spricht ausschließlich mit der FastAPI-API. Das Backend lädt offene Badegewässer-Daten aus dem Open-Data-Portal Schleswig-Holstein, ergänzt eine kleine POI-Sammlung und stellt beides als gemeinsame Karten-API bereit.

## Features

- Leaflet-Karte mit Marker-Clustering und Bounds-basiertem Nachladen
- Gemeinsame Darstellung von Badestellen und POIs auf einer Karte
- Detailzustand mit Desktop-Sidebar und mobilem Bottom Sheet
- Slug-basierte Detailrouten mit Browser-History-Synchronisierung
- Standortfunktion mit Radius-Abfrage
- Filter für Typ und Kategorie
- SSR-sichere Nuxt-3-Integration von Leaflet
- Robustes Backend mit Daten-Caching und fehlertoleranter Normalisierung

## Projektstruktur

```text
.
├── backend
│   ├── app
│   │   ├── api/routes
│   │   ├── models
│   │   └── services
│   └── pyproject.toml
├── frontend
│   ├── assets/css
│   ├── components/map
│   ├── composables
│   ├── pages
│   ├── types
│   ├── utils
│   ├── nuxt.config.ts
│   └── package.json
└── .env.example
```

## Open-Data-Quellen

Das Backend nutzt die CKAN-API des Open-Data-Portals Schleswig-Holstein und erkennt aktuelle CSV-Ressourcen automatisch. Fallback-Quellen sind hinterlegt für:

- Badegewässer Stammdaten
- Badegewässer Einstufung
- Badegewässer Infrastruktur
- Badegewässer Saisondauer
- Badegewässer Messungen

Beispielhafte aktuelle Portal-Endpunkte wurden am 5. April 2026 über die CKAN-API geprüft:

- `https://opendata.schleswig-holstein.de/api/3/action/package_search`
- `https://opendata.schleswig-holstein.de/dataset/.../download/badegewasser-stammdaten.csv`
- `http://efi2.schleswig-holstein.de/bg/opendata/v_einstufung_odata.csv`

## Voraussetzungen

- Node.js 20+
- `pnpm`
- Python 3.12+

## Entwicklung starten

### 1. Umgebungsvariablen anlegen

```bash
cp .env.example .env
```

### 2. Frontend installieren

```bash
pnpm install
```

### 3. Backend installieren

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4. Backend starten

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Frontend starten

```bash
pnpm dev:frontend
```

Frontend lokal: `http://127.0.0.1:3000`

Backend lokal: `http://127.0.0.1:8000`

## Benötigte ENV-Variablen

- `NUXT_PUBLIC_API_BASE` Basis-URL der FastAPI
- `NUXT_PUBLIC_SITE_URL` Öffentliche Basis-URL des Nuxt-Frontends für Canonical-Links
- `BACKEND_HOST`
- `BACKEND_PORT`
- `BACKEND_CORS_ORIGINS`
- `CACHE_TTL_MINUTES`
- `REQUEST_TIMEOUT_SECONDS`

## Erwartete API-Endpunkte

### `GET /api/map/v1/bounds?xmin=...&ymin=...&xmax=...&ymax=...`

Optionale Query-Parameter:

- `type=badestelle|poi`
- `category=...`

Antwort:

- GeoJSON `FeatureCollection`
- zusätzliche `filters`-Metadaten für Frontend-Filter

### `GET /api/map/v1/radius?lat=...&lng=...`

Optionale Query-Parameter:

- `radius_km=25`
- `type=badestelle|poi`
- `category=...`

### `GET /api/map/v1/details?id=...`

oder

### `GET /api/map/v1/details?slug=...`

Liefert ein normalisiertes Detailobjekt für Badestellen und POIs.

Die bestehenden Backend-Endpunkte unter `/api/bathing-sites` bleiben für die rohe Badestellen-Sicht weiter verfügbar.

### `GET /api/health`

Liefert Status, Cache-Alter, Quell-URLs und Anzahl geladener Badestellen.

## Build

Frontend-Production-Build:

```bash
pnpm build:frontend
```

## Anlehnung an die Denkmalkarte

Bewusst übernommen und fachlich auf Badestellen/POIs angepasst wurden:

- die kartenzentrierte Informationsarchitektur
- Bounds-Loading bei `moveend`
- Marker-Selection mit aktivem Markerzustand
- Intro-Zustand vs. Detail-Zustand
- Desktop-Sidebar und mobiles Bottom-Sheet
- slugbasierte Detailroute mit History-Synchronisierung
- Geolocation-Einstieg mit Radius-Abfrage

## Hinweise zur Architektur

- Leaflet initialisiert ausschließlich clientseitig in [MapView.vue](/home/awendelk/git/open-bath-map/frontend/components/map/MapView.vue).
- Die zentrale Kartenlogik liegt in [MapExperience.vue](/home/awendelk/git/open-bath-map/frontend/components/map/MapExperience.vue) plus den Composables [useMapData.ts](/home/awendelk/git/open-bath-map/frontend/composables/useMapData.ts), [useMapState.ts](/home/awendelk/git/open-bath-map/frontend/composables/useMapState.ts) und [useMapSelection.ts](/home/awendelk/git/open-bath-map/frontend/composables/useMapSelection.ts).
- Die gemeinsame Karten-API sitzt unter [map.py](/home/awendelk/git/open-bath-map/backend/app/api/routes/map.py) und nutzt die Normalisierung aus [opendata.py](/home/awendelk/git/open-bath-map/backend/app/services/opendata.py).
- Das Backend cached normalisierte Badestellen-Daten standardmäßig für sechs Stunden unter `backend/cache/`.
