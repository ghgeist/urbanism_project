<p align="center">
  <img src="assets/header_image.jpg" alt="Exploring the National Walkability Index hero image">
</p>

# Exploring the National Walkability Index

This project is a React + FastAPI app for exploring the EPA's National Walkability Index (NWI). Search a U.S. address, ZIP code, or city, choose a radius, and inspect census block group scores on an interactive map backed by PostGIS.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Walkability%20Index-009688?style=flat-square)](https://walkability-index.replit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/license/mit/)

## Overview
The National Walkability Index scores every U.S. census block group on a 1-20 scale across four dimensions: land-use mix, employment mix, street connectivity, and transit access. This app wraps that dataset in a searchable UI and a small API so you can:

- Search an address, ZIP code, or city anywhere in the United States.
- Apply buffer and search radii to explore nearby block groups.
- Inspect component scores (d2a, d2b, d3b, d4a) and the composite NWI value.

## What is here
- A React frontend with Explore, Compare, Dashboard, and Method pages.
- A FastAPI backend with geocoding and walkability summary endpoints.
- A PostGIS-backed service layer for radius queries and summary calculations.
- Data-loading scripts for building the `national_walkability_index` table from the processed source data.

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

- `frontend/` contains the React app (Vite, React Router, Leaflet) and the main UI routes.
- `api/main.py` exposes the health, geocode, and NWI summary endpoints.
- `services/db.py` handles PostgreSQL connections and pooling.
- `services/walkability.py` handles geocoding, spatial queries, and score aggregation.
- `scripts/create_neo_postgres_db.py` loads the processed CSV into PostGIS and creates the spatial index.

## Tech Stack
| Area | Tools |
| --- | --- |
| Frontend | React 19, Vite, React Router, Leaflet |
| API | FastAPI, Uvicorn |
| Geospatial | GeoPandas, Shapely, PyProj, Tenacity (backend); Leaflet (frontend) |
| Data / Infra | PostgreSQL with PostGIS (Neon, Replit, or self-hosted), SQLAlchemy, psycopg2 |
| Geocoding | Nominatim (geopy) with U.S. Census geocoder fallback |
| Testing | pytest, pytest-mock (backend); Vitest, Playwright (frontend) |
| Runtime | Python 3.11+, Node.js (frontend) |

## Quickstart
### 1. Prerequisites
- Python 3.11+
- Node.js 20+
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
Set either all `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` variables or a single `DATABASE_URL` value such as `postgresql://user:password@host:port/database`.

For local runs, use a `.env` file based on [.env.example](.env.example) and load those variables into your shell before starting the app.

### 4. Load the walkability table (one-time setup only)
The CSV is only needed for the initial load. After the data is in PostgreSQL, the app reads from the database and no longer needs the CSV file.

Create the processed file with `notebooks/compress_walkability_df.ipynb`, place it at `data/walkability_index_geospatial.csv`, or point `WALKABILITY_CSV_PATH` / `WALKABILITY_CSV_URL` at it. Then run:
```bash
python scripts/enable_postgis.py   # If your database doesn't already have PostGIS
python scripts/create_neo_postgres_db.py
```
The loader script:
- Converts WKT polygons into geometries.
- Creates the `national_walkability_index` table.
- Loads ranked component scores plus geometries.
- Builds a GIST spatial index to accelerate `ST_DWithin` queries.

After the load completes, you can remove the CSV file if you do not need to keep a local copy.

#### WAS setup (one-time)
The Walkable Accessibility Score (WAS) 2019 snapshot is loaded into a second table, `walkable_accessibility_score`, and left-joined into every query. The API and tests both tolerate the table being absent (they fall back to NWI-only responses), so this step is optional for local development but required for the Amenity Richness card and the Hollow Neighborhood banner to return real values.

1. Download the shapefile bundle from the [Credit et al. GitHub repo](https://github.com/kcredit/Walkable-Accessibility-Score) and place `US_WAS_1997_2019.shp.zip` at the repo root (or set `WAS_SHAPEFILE_PATH` / `WAS_SHAPEFILE_URL`).
2. Inspect the file without touching the database:
   ```bash
   python scripts/inspect_was_shapefile.py
   ```
3. Run the loader. It uses the same credential contract as the NWI loader and requires confirmation before it drops and rebuilds the table (use `--yes` or `WAS_LOADER_CONFIRM=1` in non-interactive environments):
   ```bash
   python scripts/load_walkable_accessibility_score.py
   ```
4. Validate both tables and summarize WAS coverage / bucket distribution:
   ```bash
   python scripts/validate_schema.py
   python scripts/summarize_was_distribution.py
   ```

The summary script reports the current WAS row count, direct NWI join rate,
score distribution, and Amenity Richness bucket counts for the connected
database. Amenity Richness uses rounded WAS cutoffs of 10 and 20 as practical
interpretation breakpoints; see `docs/sessions/active/2026-04-17-was-integration.md`
for the shared database values observed during the WAS analytics follow-up.

**Connecting from your laptop vs. a managed runtime:** if your Postgres is hosted on Replit or Neon, the "internal" hostname (e.g. `helium`) does not resolve off-platform. Use the external/public URL from the Neon console or Replit's "External URL" setting when running the loader locally, or run the loader from within the Replit environment where the internal hostname does resolve.

### 5. Run the app locally
With the virtual environment activated, start the API from the project root:
```bash
uvicorn api.main:app --reload
```
Then start the frontend in a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` (or the URL Vite prints). The frontend calls `http://127.0.0.1:8000` by default; set `VITE_API_URL` if your API runs somewhere else.

If you are on Unix, macOS, or Git Bash, you can also run `./scripts/run_dev.sh` from the project root to start both services together. On Windows without Bash, use two terminals.

## Usage

The app has four main routes:

- **Explore** (`/`): Search any U.S. address, ZIP code, or city and view walkability metrics on an interactive map. Set buffer and search radii to explore nearby census block groups.
- **Compare** (`/compare`): Side-by-side comparison of two locations with summary panels and metric differences.
- **Dashboard** (`/dashboard`): Component analysis dashboard with visualizations showing distributions, correlations, contributions, and comparisons of the four NWI components (D2A, D2B, D3B, D4A).
- **Method** (`/method`): Documentation about the National Walkability Index methodology and data sources.

The main controls are:
- `Radius`: the area shown around the selected location.
- `Search radius`: the optional surrounding area used to look for nearby better-scoring block groups.
- `Minimum NWI improvement delta`: the threshold for flagging better nearby candidates.

## API (FastAPI)
### Run locally
See [Quickstart](#5-run-the-app-locally) for the full app startup. To run only the API:
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
API errors use a consistent JSON shape:
```json
{
  "code": "location_not_found",
  "message": "Location not found.",
  "details": {
    "query": "Nowhere, ZZ"
  }
}
```

Common examples:
- `location_not_found` (404) for unknown geocode/query lookups
- `invalid_request` (400) for service-level validation failures
- `validation_error` (422) for request parameter validation failures
- `service_unavailable` (503) for temporary database connectivity failures

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
- **Replit:** The live app runs at [walkability-index.replit.app](https://walkability-index.replit.app/). The deployed app serves the API and the built frontend from the same FastAPI process, which keeps the deployment simple on Replit's single exposed port. See `replit.md` for setup details.
- **Self-managed:** Run FastAPI and serve the built frontend from `frontend/dist/`, with access to PostgreSQL/PostGIS and HTTPS in front of the app.

### Production notes
If you deploy this publicly:

1. Set `API_CORS_ORIGINS` to your frontend origin or origins. The default list is for localhost development only.
2. Leave `WALKABILITY_DEBUG_LOG` unset in production.
3. Run `pip-audit` periodically if you want an extra dependency check outside CI.

## Data Pipeline
- Source datasets:
  - [Walkability Index](https://catalog.data.gov/dataset/walkability-index3) — EPA NWI (primary).
  - [FIPS Codes](https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt)
  - [Smart Location Mapping](https://www.epa.gov/smartgrowth/smart-location-mapping#walkability)
  - [Walkable Accessibility Score (WAS) 1997-2019](https://github.com/kcredit/Walkable-Accessibility-Score) — used here as a complementary amenity-density signal. Only the 2019 snapshot is loaded today.
- `notebooks/compress_walkability_df.ipynb` simplifies geometries, drops unneeded rows, and reduces the table size before loading.
- Files in `data/` feed the ingestion script.

### Citing the data
- **EPA NWI:** EPA Office of Sustainable Communities, *National Walkability Index User Guide and Methodology* (2021).
- **WAS:** Credit, K., Farah, I., Talen, E., Anselin, L., & Ghomrawi, H. (2025). The Walkable Accessibility Score (WAS): A spatially-granular open-source measure of walkability for the continental US from 1997-2019. *Environment and Planning B*. DOI: [10.1177/23998083251377116](https://doi.org/10.1177/23998083251377116). Source: [github.com/kcredit/Walkable-Accessibility-Score](https://github.com/kcredit/Walkable-Accessibility-Score).

## Testing & Validation

For fuller testing notes, see [`docs/TESTING.md`](docs/TESTING.md).

- Backend tests: run `pytest`. The Python tests use mocks and do not require a live database connection. See `tests/README.md` for backend details.
- Frontend tests: run `cd frontend && npm run test:run` for unit tests and `npm run e2e:run` for Playwright coverage.
  `jsdom` is pinned to `26.1.0` because the current Node `20.18.2` runtime cannot run `jsdom@28`'s transitive `require(ESM)` path.
- Python lint: run `python -m ruff check --no-cache api services scripts tests`.
- Frontend typecheck and lint: run `cd frontend && npx tsc --noEmit && npm run lint`.
- Schema validation: run `python scripts/validate_schema.py`.
- Config validation: run `python scripts/check_config.py`.
- Smoke test: start the API and frontend, search for `Knoxville, TN`, and confirm the map and summary data render.

---

This project is part of a broader geospatial full-stack portfolio. More background is available at [grantgeist.com](https://grantgeist.com/).

## License
[MIT License](https://opensource.org/license/mit/)
