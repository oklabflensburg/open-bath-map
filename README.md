# Open Bath Map

Interaktive Open-Data-Kartenanwendung für Badestellen und wassernahe POIs in Schleswig-Holstein.

![Screenshot der Badestellenkarte](./screenshot_badestellenkarte.webp)

## Überblick

Open Bath Map besteht aus einem Nuxt-3-Frontend und einem FastAPI-Backend. Das Backend lädt offene Badegewässerdaten des Landes Schleswig-Holstein, ergänzt sie um wassernahe touristische POIs, normalisiert beide Quellen und stellt sie über eine gemeinsame Karten-API bereit. Das Frontend rendert darauf eine Leaflet-Karte mit SSR-fähigen Detailseiten, Suchfunktion, Filtern, JSON+LD und PWA-Bausteinen.

Der aktuelle Fokus des Repos liegt auf einer kartenzentrierten API. Die frühere fachliche `/api/bathing-sites`-Schiene ist entfernt. Das Frontend nutzt ausschließlich `/api/map/v1/*` sowie `/api/health`.

## Funktionen

- Interaktive Karte für Badestellen und zusätzliche wassernahe POIs
- Bounds-basierte Marker-Abfrage für den sichtbaren Kartenausschnitt
- Radius-Suche auf Basis des Browser-Standorts
- Volltextsuche mit Typ-, Kategorie- und Infrastrukturfiltern
- SEO-fähige Detailseiten unter sprechenden Slugs
- JSON+LD und Open-Graph-Metadaten pro Detailseite
- Bild-Fallbacks für nicht erreichbare Bilder
- Desktop-Sidebar und mobiles Bottom Sheet mit tab-basierter Navigation
- PWA-Grundausstattung mit Manifest und Service Worker
- Optionale PostgreSQL-/PostGIS-Persistenz mit Volltext- und Trigramm-Suche

## Architektur

### Frontend

Das Frontend liegt unter [`frontend`](./frontend) und ist ein Nuxt-3-Projekt mit Vue 3, TypeScript, Tailwind CSS, Leaflet und `leaflet.markercluster`.

Wichtige Bausteine:

- [`frontend/pages/[[slug]].vue`](./frontend/pages/[[slug]].vue): SSR-Einstiegspunkt für Karten- und Detailseiten, inklusive SEO-Metadaten und JSON+LD
- [`frontend/components/map/MapExperience.vue`](./frontend/components/map/MapExperience.vue): zentrale Orchestrierung von Karte, Sidebar, Bottom Sheet, Suche und Auswahlzustand
- [`frontend/components/map/MapView.vue`](./frontend/components/map/MapView.vue): Leaflet-Karte mit Marker-Rendering und Interaktionen
- [`frontend/components/map/MapSidebar.vue`](./frontend/components/map/MapSidebar.vue): Desktop-Navigation für Info, Suche/Filter und Markerdetails
- [`frontend/components/map/MapBottomSheet.vue`](./frontend/components/map/MapBottomSheet.vue): mobile Entsprechung zur Sidebar
- [`frontend/composables/useMapData.ts`](./frontend/composables/useMapData.ts): API-Zugriffe auf Bounds, Radius, Detaildaten und Suche
- [`frontend/composables/useMapSelection.ts`](./frontend/composables/useMapSelection.ts): Synchronisierung von Marker-Auswahl und slug-basierter Route
- [`frontend/composables/useMapState.ts`](./frontend/composables/useMapState.ts): globaler Karten- und UI-Zustand
- [`frontend/composables/useJsonLd.ts`](./frontend/composables/useJsonLd.ts): Einbindung strukturierter Daten
- [`frontend/composables/useImageFallback.ts`](./frontend/composables/useImageFallback.ts): Fallback bei defekten Bild-URLs

### Backend

Das Backend liegt unter [`backend`](./backend) und ist ein FastAPI-Dienst mit SQLModel/SQLAlchemy, optionaler PostgreSQL-Persistenz und PostGIS-Unterstützung.

Wichtige Bausteine:

- [`backend/app/main.py`](./backend/app/main.py): FastAPI-App und Router-Registrierung
- [`backend/app/api/routes/map.py`](./backend/app/api/routes/map.py): Karten-Endpunkte
- [`backend/app/api/routes/health.py`](./backend/app/api/routes/health.py): Health-Endpunkt
- [`backend/app/services/opendata/service.py`](./backend/app/services/opendata/service.py): Discovery, Download, Normalisierung und Mapping der Open-Data-Quellen
- [`backend/app/services/postgres_store.py`](./backend/app/services/postgres_store.py): Persistenz, Suche und Kartenabfragen auf PostgreSQL/PostGIS
- [`backend/app/db/models.py`](./backend/app/db/models.py): SQLModel-Tabellen für Datensatzstatus, Badestellen und Kartenobjekte
- [`backend/app/db/session.py`](./backend/app/db/session.py): Engine-, Session- und Support-Objekt-Verwaltung für PostgreSQL
- [`backend/app/services/opendata/source_queries.toml`](./backend/app/services/opendata/source_queries.toml): konfigurierbare CKAN-/Fallback-Quellen

## Datenquellen und Datenfluss

### Quellen

Die Badestellen werden aus mehreren CSV-Quellen des Landes Schleswig-Holstein zusammengesetzt:

- Stammdaten
- Einstufung
- Infrastruktur
- Saisondauer
- Messungen

Zusätzlich werden wassernahe touristische POIs aus der touristischen Landesdatenbank eingebunden.

Die Quellkonfiguration liegt in [`backend/app/services/opendata/source_queries.toml`](./backend/app/services/opendata/source_queries.toml). Die CKAN-Basis-URL wird ebenfalls daraus gelesen. Falls die CKAN-Discovery keine passende Ressource liefert, verwendet der Service direkte EFI-Fallback-URLs.

### Ablauf

1. Das Frontend lädt Marker über Bounds-, Radius- oder Suchanfragen.
2. Das Backend liest Daten entweder direkt aus dem Cache/den Open-Data-Quellen oder aus PostgreSQL, wenn `DATABASE_URL` gesetzt ist.
3. Die Open-Data-Schicht normalisiert Badegewässerdaten und leitet daraus `MapItem`-Objekte ab.
4. Wassernahe POIs werden ergänzt und mit den Badestellen in einer gemeinsamen Kartenrepräsentation zusammengeführt.
5. Detailseiten werden unter `/<slug>` serverseitig vorbereitet, damit SEO-Metadaten und JSON+LD bereits im ersten HTML enthalten sind.

## API

### `GET /api/health`

Liefert Status, Cache-Alter, Sync-Zeitpunkt, Quell-URLs und die Anzahl der aktuell verfügbaren Datensätze.

### `GET /api/map/v1/bounds`

Liefert Marker für einen Kartenausschnitt.

Query-Parameter:

- `xmin`
- `ymin`
- `xmax`
- `ymax`
- `type`: `badestelle` oder `poi`
- `category`
- `infrastructure`

### `GET /api/map/v1/radius`

Liefert Marker im Umkreis eines Punktes.

Query-Parameter:

- `lat`
- `lng`
- `radius_km`
- `type`
- `category`
- `infrastructure`

### `GET /api/map/v1/details`

Liefert ein einzelnes Kartenobjekt.

Query-Parameter:

- `id` oder
- `slug`

### `GET /api/map/v1/search`

Volltextsuche über Kartenobjekte mit optionalen Filtern.

Query-Parameter:

- `q`
- `type`
- `category`
- `infrastructure`
- `limit`

## Repository-Struktur

```text
.
├── backend
│   ├── alembic
│   │   └── versions
│   ├── app
│   │   ├── api/routes
│   │   ├── db
│   │   ├── models
│   │   └── services
│   │       └── opendata
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend
│   ├── assets/css
│   ├── components
│   │   ├── map
│   │   └── site
│   ├── composables
│   ├── pages
│   ├── public
│   ├── types
│   ├── utils
│   ├── app.vue
│   ├── nuxt.config.ts
│   └── package.json
├── scripts
│   ├── generate_sitemap.py
│   └── sync_postgres.py
├── .env.example
├── package.json
└── pnpm-workspace.yaml
```

## Voraussetzungen

- Node.js 20+
- `pnpm`
- Python 3.12+
- Optional für Persistenz und Suche: PostgreSQL mit PostGIS

## Setup

### 1. Umgebungsvariablen anlegen

```bash
cp .env.example .env
```

### 2. Frontend-Abhängigkeiten installieren

```bash
pnpm --dir frontend install
```

### 3. Backend-Venv anlegen und Abhängigkeiten installieren

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Lokale Entwicklung

### Backend starten

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend starten

```bash
pnpm dev:frontend
```

Lokale Standard-URLs:

- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:8000`

## Betriebsmodi des Backends

### Ohne PostgreSQL

Wenn `DATABASE_URL` nicht gesetzt ist, lädt das Backend Daten direkt aus den Open-Data-Quellen und verwendet den lokalen JSON-Cache unter `backend/cache`.

Das ist für Entwicklung und schnelles Testen ausreichend.

### Mit PostgreSQL/PostGIS

Wenn `DATABASE_URL` gesetzt ist, verwendet die API den PostgreSQL-Store. Dabei werden PostGIS-, `unaccent`- und `pg_trgm`-Supportobjekte automatisch angelegt. Suche und Kartenabfragen laufen dann gegen die Datenbank.

Den Datenbestand kannst du mit folgendem Script synchronisieren:

```bash
pnpm sync:postgres
```

Das Script lädt die Open-Data-Quellen, normalisiert sie und schreibt Badestellen sowie Kartenobjekte nach PostgreSQL.

## Datenbankmigrationen

Das Repo enthält Alembic-Migrationen unter [`backend/alembic/versions`](./backend/alembic/versions).

Migrationen anwenden:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Wichtig: Für Migrations- und Sync-Betrieb muss `DATABASE_URL` gesetzt sein.

## Nützliche Skripte

Frontend starten:

```bash
pnpm dev:frontend
```

Frontend-Produktionsbuild:

```bash
pnpm build:frontend
```

Frontend-Vorschau:

```bash
pnpm preview:frontend
```

Nuxt-Typecheck:

```bash
pnpm --dir frontend typecheck
```

PostgreSQL-Sync:

```bash
pnpm sync:postgres
```

Sitemap generieren:

```bash
pnpm generate:sitemap
```

Die Sitemap wird nach [`frontend/public/sitemap.xml`](./frontend/public/sitemap.xml) geschrieben.

## Umgebungsvariablen

### Frontend

| Variable | Bedeutung |
| --- | --- |
| `NUXT_PUBLIC_API_BASE` | Basis-URL des FastAPI-Backends |
| `NUXT_PUBLIC_SITE_URL` | Öffentliche Basis-URL des Frontends für Canonicals, Sitemap und SEO |
| `NUXT_PUBLIC_CONTACT_MAIL` | Kontakt-E-Mail für Impressum und Datenschutz |
| `NUXT_PUBLIC_CONTACT_PHONE` | Telefonnummer für das Impressum |
| `NUXT_PUBLIC_PRIVACY_CONTACT_PERSON` | Verantwortliche Person für Datenschutzangaben |
| `NUXT_PUBLIC_ADDRESS_NAME` | Name der Organisation |
| `NUXT_PUBLIC_ADDRESS_STREET` | Straße |
| `NUXT_PUBLIC_ADDRESS_HOUSE_NUMBER` | Hausnummer |
| `NUXT_PUBLIC_ADDRESS_POSTAL_CODE` | Postleitzahl |
| `NUXT_PUBLIC_ADDRESS_CITY` | Ort |

### Backend

| Variable | Bedeutung |
| --- | --- |
| `BACKEND_HOST` | Host für den FastAPI-Server |
| `BACKEND_PORT` | Port für den FastAPI-Server |
| `BACKEND_CORS_ORIGINS` | Kommaseparierte Liste erlaubter Origins |
| `CACHE_TTL_MINUTES` | Gültigkeit des Datei-Caches in Minuten |
| `REQUEST_TIMEOUT_SECONDS` | Timeout für Requests auf externe Datenquellen |
| `DATABASE_URL` | Optionale PostgreSQL-Verbindung; wenn gesetzt, liest die API primär aus der Datenbank |

## SEO und Auslieferung

- Detailseiten werden serverseitig über [`frontend/pages/[[slug]].vue`](./frontend/pages/[[slug]].vue) vorbereitet.
- `useSeoMeta` setzt Titel, Beschreibung und Open-Graph-Bilder abhängig vom gewählten Kartenobjekt.
- JSON+LD wird pro Route erzeugt.
- Die Sitemap wird per [`scripts/generate_sitemap.py`](./scripts/generate_sitemap.py) generiert.
- Das Frontend ist als Nuxt-Anwendung mit PWA-Manifest und Service Worker konfiguriert.

## Hinweise für Maintainer

- Die fachliche Quellkonfiguration liegt in [`backend/app/services/opendata/source_queries.toml`](./backend/app/services/opendata/source_queries.toml), nicht mehr hartkodiert in Python.
- Bilder für Badestellen werden aus Kennzeichen/Datensatzlogik serverseitig erzeugt; im Frontend existiert zusätzlich ein Dummy-Fallback.
- Das Repo enthält generierte Artefakte wie `frontend/.nuxt`, `frontend/.output` und lokale Virtualenv-/Node-Module-Verzeichnisse. Diese sind keine sinnvolle Quelle für Architekturentscheidungen; maßgeblich sind die Dateien unter `frontend/`, `backend/` und `scripts/`.
