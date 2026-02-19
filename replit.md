# Exploring the U.S. National Walkability Index

## Overview
This is a React + FastAPI application that visualizes the EPA's National Walkability Index (NWI) on an interactive map. Users can search for any U.S. address, ZIP code, or city and explore walkability scores for nearby census block groups.

**Live app:** [walkability-index.replit.app](https://walkability-index.replit.app/)

## Project Structure
```
├── frontend/                  # React (Vite) app — map, search, summary
├── api/                       # FastAPI app — health, geocode, NWI summary
├── services/
│   ├── db.py                  # DB connection factory
│   └── walkability.py        # Geocoding, PostGIS queries, profile computation
├── scripts/
│   ├── enable_postgis.py     # Enable PostGIS in PostgreSQL
│   └── create_neo_postgres_db.py  # One-time DB load from CSV
├── notebooks/                 # Jupyter notebooks for data processing
└── data/                      # Processed artifacts (e.g. CSV for ingestion)
```

## Tech Stack
- **Frontend**: React 19, Vite, React Router, Leaflet
- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL with PostGIS extension
- **Geospatial**: GeoPandas, Shapely, PyProj (backend); Leaflet (frontend)
- **Geocoding**: Geopy (Nominatim)

## Running the App on Replit
Two workflows run in parallel:
- **React Frontend** (port 5000, webview): `cd frontend && npm install && npm run dev`
- **FastAPI Backend** (port 8000, console): `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`

The Vite dev server proxies API requests (`/health`, `/geocode`, `/nwi`) to the backend on port 8000. For production, see **Replit deployment (below)**.

**Dev vs prod ports:** Production uses a single process on Replit’s `PORT`. The Run workflow uses 8000. If you’re developing via SSH and the Run workflow is already using 8000, start the backend on a different port (e.g. `uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload`) and point the frontend proxy or `VITE_API_URL` at 8001 if needed.

### Replit deployment best practices (review)

- **Use `PORT`:** The deployment run command uses `uvicorn ... --port ${PORT:-8000}` so the app binds to Replit’s assigned port. Replit sets `PORT` in deployment; your app must listen on it so the platform can route traffic.
- **Bind to `0.0.0.0`:** The server uses `--host 0.0.0.0` so it’s reachable from Replit’s proxy (not only localhost).
- **Single process, single port:** Autoscale deployments support only **one** external port. The deployment runs a single process (FastAPI) that serves both the API and the built React app from `frontend/dist`. The build step runs `npm run build`; at run time, if `frontend/dist` exists, FastAPI mounts it so the same origin serves the SPA and the API (no CORS or second port).
- **[[ports]] in .replit:** Multiple `externalPort` entries are for the workspace (Run/Preview). For published autoscale apps, only the default port (e.g. 80) is exposed; the single `run` process listens on `PORT`.

## Database Requirements
The app requires a PostgreSQL database with PostGIS extension and a `national_walkability_index` table. Table structure:
- geoid20: Census block group ID
- d2a_ranked, d2b_ranked, d3b_ranked, d4a_ranked: Component scores
- natwalkind: Composite walkability index (1-20)
- geometry: PostGIS geometry (EPSG:4326)

## Data Loading
To populate the database (one-time setup):
1. Download from: https://catalog.data.gov/dataset/walkability-index3
2. Process with `notebooks/compress_walkability_df.ipynb`
3. Load using:
   ```bash
   python scripts/create_neo_postgres_db.py
   ```
   Set `WALKABILITY_CSV_URL` or `WALKABILITY_CSV_PATH` if the CSV is not at `data/walkability_index_geospatial.csv`.

**Note:** Once the database is populated, the CSV is no longer needed. The application queries PostgreSQL directly.

## Configuration

### Database Setup (Replit PostgreSQL)

1. **Enable PostgreSQL in Replit:**
   - Open the Secrets tab (🔒 icon in sidebar)
   - Replit will auto-generate PostgreSQL credentials
   - Environment variables: `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`

2. **Enable PostGIS extension:**
   ```bash
   python scripts/enable_postgis.py
   ```

3. **Load the walkability data (one-time setup):**
   Set `WALKABILITY_CSV_URL` (or `WALKABILITY_CSV_PATH`) in Secrets if needed, then:
   ```bash
   python scripts/create_neo_postgres_db.py
   ```
   After successful setup, you can remove the CSV URL and the app will use only the database.

### Backward Compatibility
The backend reads `PG*` environment variables (or `DATABASE_URL`). Replit Secrets and any env configuration (e.g. `.env` for local dev) are supported.
