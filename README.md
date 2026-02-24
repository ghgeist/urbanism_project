<p align="center">
  <img src="assets/header_image.jpg" alt="Exploring the National Walkability Index hero image">
</p>

# Exploring the National Walkability Index

A **portfolio project**: a geospatial web app that makes the EPA’s National Walkability Index (NWI) easy to explore. Search any U.S. location, set a buffer, and view walkability at the census block group level on an interactive map—backed by PostGIS and a REST API for reuse in other tools.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Walkability%20Index-009688?style=flat-square)](https://walkability-index.replit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/license/mit/)

## Table of Contents
1. [Overview](#overview)
2. [Project Highlights](#project-highlights)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Quickstart](#quickstart)
6. [Usage](#usage)
7. [API (FastAPI)](#api-fastapi)
8. [Deployment](#deployment)
9. [Data Pipeline](#data-pipeline)
10. [Testing & Validation](#testing--validation)
11. [Contributing](#contributing)
12. [Roadmap](#roadmap)
13. [License](#license)

## Overview
The National Walkability Index (NWI) scores every U.S. census block group on a 1–20 scale across four dimensions: land-use mix, employment mix, street connectivity, and transit access. This project wraps the dataset in a React app + FastAPI backend so planners, advocates, and curious residents can:

- Search an address, ZIP code, or city anywhere in the United States.
- Apply buffer and search radii to explore nearby block groups.
- Inspect component scores (d2a, d2b, d3b, d4a) and the composite NWI value.

## Project Highlights
- **Geospatial stack**: PostGIS spatial queries (`ST_DWithin`), GeoPandas, latitude-aware distance conversion; Leaflet for interactive maps.
- **Full-stack scope**: React (Vite) frontend, FastAPI backend with geocode + NWI summary endpoints.
- **Production-minded**: Cached DB connections with reconnection handling, structured error responses, pytest coverage, schema and config validation scripts.
- **Open data**: EPA NWI + FIPS and Smart Location Mapping; reproducible pipeline from source data to hosted PostGIS.

## Architecture
```
React (Vite) frontend              FastAPI
        │                              │
        └──────────────┬───────────────┘
                       ▼
        Walkability service layer (`services/walkability.py`)
                       │
                       ▼
        PostgreSQL + PostGIS (national_walkability_index table)
```

- **`frontend/`** — React app (Vite, React Router, Leaflet): search, radius/delta controls, interactive map, and summary table. Includes three routes: Explore (main search), Compare (side-by-side), and Method (documentation).
- **`api/main.py`** — FastAPI app: health, geocode, and NWI summary endpoints consumed by the frontend.
- **`services/db.py`** — Framework-agnostic DB connection factory (env vars only).
- **`services/walkability.py`** — Geocoding (Nominatim), PostGIS queries, profile computation.
- **`scripts/create_neo_postgres_db.py`** — One-time load of processed CSV into PostGIS and spatial index creation.

## Tech Stack
| Area | Tools |
| --- | --- |
| Frontend | React 19, Vite, React Router, Leaflet |
| API | FastAPI, Uvicorn |
| Geospatial | GeoPandas, Shapely, PyProj, Tenacity (backend); Leaflet (frontend) |
| Data / Infra | PostgreSQL with PostGIS (Neon, Replit, or self-hosted), SQLAlchemy, psycopg2 |
| Geocoding | Nominatim (geopy) |
| Testing | pytest, pytest-mock (backend); Vitest, Playwright (frontend) |
| Runtime | Python 3.11+, Node.js (frontend) |

## Quickstart
### 1. Prerequisites
- Python 3.11+
- Git
- Access to a PostgreSQL database with PostGIS enabled (Neon, Replit, or self-hosted)

### 2. Clone & install
```bash
git clone https://github.com/ghgeist/urbanism_project.git
cd urbanism_project
python -m venv .venv
# Activate the venv: Windows → .\.venv\Scripts\activate   Unix/macOS → source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure database connection
Set either **all** of `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` **or** a single `DATABASE_URL` (e.g. `postgresql://user:password@host:port/database`). All core services read these env vars exclusively.

**Local runs:** Use a local `.env` (see root [.env.example](.env.example)) and load vars in your shell before running commands.

### 4. Load the walkability table (one-time setup only)
> **Important:** The CSV file is only needed for initial database setup. Once the database is populated, you can remove the CSV file. The running application queries PostgreSQL directly and does not use the CSV file.

**Data authority note:**  
This repository treats the PostgreSQL/PostGIS database as the authoritative data source for the running application.  
The original tabular CSV used for seeding (~39 MB) is intentionally not committed to the repository after setup.  
For this portfolio deployment, the dataset lives in:
- the hosted PostGIS database (Replit)
- a separate cold backup (e.g., Google Drive)

The repo contains the ingestion logic, schema, and validation scripts required to reload the data if needed.

The repository bundles a simplified CSV produced by `notebooks/compress_walkability_df.ipynb`. Place the output at `data/walkability_index_geospatial.csv`, or set `WALKABILITY_CSV_PATH` (or `WALKABILITY_CSV_URL`) to your file or URL. Then, with the env vars above set, run:
```bash
python scripts/enable_postgis.py   # If your database doesn't already have PostGIS
python scripts/create_neo_postgres_db.py
```
The script:
- Converts WKT polygons into geometries.
- Creates the `national_walkability_index` table.
- Loads ranked component scores plus geometries.
- Builds a GIST spatial index to accelerate `ST_DWithin` queries.

After successful setup, you can safely delete the CSV file and any `WALKABILITY_CSV_URL` environment variables. The application will continue to work using only the PostgreSQL database.

### 5. Run the app locally
With your venv activated, start the **API** (from project root):
```bash
uvicorn api.main:app --reload
```
Then start the **React frontend** (from another terminal, in `frontend/`):
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 (or the URL Vite prints). The frontend uses the API at http://127.0.0.1:8000 by default; set `VITE_API_URL` if your API runs elsewhere.

**One-command option (Unix/macOS or Git Bash):** From the project root run `./scripts/run_dev.sh` (or `bash scripts/run_dev.sh`) to start both the API and the frontend; Ctrl+C stops both. On Windows without Bash, start the API and frontend in two terminals as above.

## Usage

The app includes four main pages accessible via navigation:

- **Explore** (`/`): Search any U.S. address, ZIP code, or city and view walkability metrics on an interactive map. Set buffer and search radii to explore nearby census block groups.
- **Compare** (`/compare`): Side-by-side comparison of two locations with summary panels and metric differences.
- **Dashboard** (`/dashboard`): Component analysis dashboard with visualizations showing distributions, correlations, contributions, and comparisons of the four NWI components (D2A, D2B, D3B, D4A).
- **Method** (`/method`): Documentation about the National Walkability Index methodology and data sources.

### Key Features
- **Radius** (0.1-3.0 miles in current UI): area shown around the selected location.
- **Search radius** (API parameter): optional context radius used for nearby-better detection; defaults to selected radius when omitted.
- **Minimum NWI improvement delta**: filter/highlight threshold for nearby-better candidates.
- Interactive map centers on the selected location with a marker and radius context; summary and table views expose component ranks (`d2a`, `d2b`, `d3b`, `d4a`) and composite NWI metrics.

## API (FastAPI)
### Run locally
See [Quickstart](#5-run-the-app-locally) for full app startup. **API only** (e.g. for Swagger/ReDoc), from the project root with venv activated:
```bash
uvicorn api.main:app --reload
```

Interactive docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Endpoints
- `GET /health`
  - Returns service health status.
- `GET /geocode?q=Knoxville,%20TN`
  - Returns `{ lat, lon, label }` for a query string.
- `GET /nwi/summary?lat=35.9606&lon=-83.9207&selected_radius_miles=1.0&search_radius_miles=3.0&min_delta=2.0&top_n=3`
  - Returns the canonical summary profile for explicit coordinates.
- `GET /nwi/summary/by-query?q=Knoxville,%20TN&selected_radius_miles=1.0&search_radius_miles=3.0&min_delta=2.0&top_n=3`
  - One-call geocode + summary endpoint for frontend use.

### Error envelope
All API errors return a consistent JSON shape:
```json
{
  "code": "location_not_found",
  "message": "Location not found.",
  "details": {
    "query": "Nowhere, ZZ"
  }
}
```

Examples:
- `location_not_found` (404) for unknown geocode/query lookups
- `invalid_request` (400) for service-level validation failures
- `validation_error` (422) for request parameter validation failures

### CORS configuration
Default allowed origins:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:5000`
- `http://127.0.0.1:5000`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

Override with `API_CORS_ORIGINS` (comma-separated):
```bash
API_CORS_ORIGINS=http://localhost:3000,https://your-frontend.example
```

## Deployment
- **Replit:** The live app runs at [walkability-index.replit.app](https://walkability-index.replit.app/). A single process serves both the API and the built React app from the same origin (FastAPI mounts `frontend/dist` when present), so Replit’s one-port deployment works without CORS. Configure Replit PostgreSQL (or a connected Neon/Supabase DB) via Secrets; see `replit.md` for Run workflow and deployment best practices.
- **Self-managed:** Run the FastAPI app (e.g. `uvicorn api.main:app`) and serve the built React app (e.g. `frontend/dist/`) with access to PostgreSQL/PostGIS. Use HTTPS and secure handling of secrets.

### Production checklist (minimal)
When deploying to a public URL (e.g. Replit, Vercel + your API host):

1. **CORS:** Set `API_CORS_ORIGINS` to your frontend origin(s), e.g. `https://walkability-index.replit.app`. Defaults are localhost-only.
2. **Debug logging:** Do not set `WALKABILITY_DEBUG_LOG` in production; it can log request-related data. Omit the variable or leave it unset.
3. **Dependencies:** Periodically run `pip-audit` (install with `pip install pip-audit`) to check for known vulnerabilities. Fix criticals when convenient; this is not wired into CI so it won’t block shipping.

## Data Pipeline
- Source datasets:
  - [Walkability Index](https://catalog.data.gov/dataset/walkability-index3)
  - [FIPS Codes](https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt)
  - [Smart Location Mapping](https://www.epa.gov/smartgrowth/smart-location-mapping#walkability)
- `notebooks/compress_walkability_df.ipynb`:
  - Simplifies geometries to keep the PostGIS table under Neon size limits.
  - Drops non-CBSA rows and optimizes column types.
  - Estimates target table footprint to avoid overages.
- Processed artifacts live in `data/` and feed the ingestion script.

## Testing & Validation

> **📖 For comprehensive testing documentation, see [`docs/TESTING.md`](docs/TESTING.md)**

- **Automated test suite:** 
  - **Backend**: Run `pytest` for Python/FastAPI tests (100+ tests): input validation, distance conversion, geocoding, data fetching, API endpoints, and profile metric invariants. Tests use mocks and don't require a live database connection. See `tests/README.md` for backend-specific details.
  - **Frontend**: Run `cd frontend && npm run test:run` for React/TypeScript unit tests (Vitest + React Testing Library) and `npm run e2e:run` for E2E tests (Playwright).
- **Python linting (Ruff):** Run `python -m ruff check --no-cache api services scripts tests` for lint checks. Use `python -m ruff check --no-cache --fix api services scripts tests` for safe autofixes.
- **TypeScript/ESLint:** Run `cd frontend && npx tsc --noEmit && npm run lint` to check types and lint frontend code.
- **Schema validation:** Run `python scripts/validate_schema.py` to verify database table structure, spatial indexes, and PostGIS extension.
- **Configuration check:** Run `python scripts/check_config.py` to validate required environment variables are present.
- **Manual smoke test:** start the API and React app (see Quickstart), open the app in the browser, query "Knoxville, TN", and confirm the map and summary table populate.
- **Data sanity checks:** when `WALKABILITY_DEBUG_LOG=1` is set, inspect API stdout/logs for geocoding errors; verify `national_walkability_index` counts in Postgres (`SELECT COUNT(*) ...`).

---

## Contributing

This is an **experimental project** designed for fast iteration while maintaining quality. Both humans and AI coding agents are welcome!

**Quick start:**
- See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development workflow
- See [`AGENTS.md`](AGENTS.md) for AI agent guidelines
- See [`CLAUDE.md`](CLAUDE.md) for project-specific context

**Before committing:**
- Run `./scripts/quick_check.sh` (Unix/macOS) or `.\scripts\quick_check.ps1` (Windows) to validate all checks
- Or rely on CI - GitHub Actions will catch issues automatically on push/PR

**Key principles:**
- ✅ Fast iteration + automated safety nets
- ✅ Type safety enforced by CI
- ✅ Clear patterns documented in `docs/dev_notes/lessons.md`
- ✅ Session-based work tracking in `docs/sessions/`

---

*This project is part of a portfolio demonstrating geospatial full-stack development with open government data. For more, see [grantgeist.com](https://grantgeist.com/).*

## License
[MIT License](https://opensource.org/license/mit/)
