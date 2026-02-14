# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Streamlit geospatial application that visualizes the EPA's National Walkability Index (NWI) dataset. Users search any U.S. address, ZIP code, or city, apply a buffer radius, and view an interactive Folium choropleth map colored by walkability scores (1-20 scale) at the Census block group level.

## Tech Stack

- **Runtime**: Python 3.11+
- **UI**: Streamlit + streamlit-folium
- **Geospatial**: GeoPandas, Folium, Shapely, PyProj
- **Database**: PostgreSQL with PostGIS (Replit PostgreSQL or Neon)
- **Geocoding**: Nominatim via geopy (with tenacity retry logic)
- **DB drivers**: psycopg2-binary, SQLAlchemy

## Common Commands

```bash
# Run the app
streamlit run app.py

# Run all tests
pytest

# Run tests verbose
pytest -v

# Run a specific test class
pytest tests/test_walkability.py::TestInputValidation

# Run a single test
pytest tests/test_walkability.py::TestInputValidation::test_valid_city_name

# Run with coverage
pytest --cov=services --cov-report=html

# Database setup (one-time, in order)
python scripts/enable_postgis.py
streamlit run scripts/create_neo_postgres_db.py
```

## Architecture

```
app.py                          # Entry point: page config + orchestrates sidebar/map
├── components/sidebar.py       # User inputs (address, buffer radius slider)
├── components/map_display.py   # Connection caching, data fetching, map rendering
└── services/
    ├── db.py                   # Framework-agnostic DB connection factory (env vars only)
    └── walkability.py          # Core logic: geocoding, DB queries, map creation
```

**Request flow**: User enters address in sidebar → `map_display.py` calls geocoding and DB query (with `@st.cache_resource` caching) → `walkability.py` geocodes via Nominatim, runs PostGIS spatial query with buffer → returns GeoDataFrame → `map_display.py` renders Folium choropleth + data table.

**Connection handling**: `map_display.py` manages a cached DB connection (`get_cached_db_connection()`). It detects closed connections, clears the Streamlit cache, and retries automatically. Structured JSON debug logging is available via `WALKABILITY_DEBUG_LOG=1`.

**Database**: Single table `national_walkability_index` with columns: `geoid20` (PK), `d2a_ranked`, `d2b_ranked`, `d3b_ranked`, `d4a_ranked`, `natwalkind` (all NUMERIC(4,2)), and `geometry` (PostGIS GEOMETRY, SRID 4326). Loaded from `data/walkability_index_tabular.csv` (~203k rows).

## Key Implementation Details

- `db.py:get_db_connection()` reads `PG*` env vars exclusively (no Streamlit dependency). `validate_pg_env()` and `get_pg_env()` are reusable validators shared by scripts
- `walkability.py:get_walkability_data()` accepts psycopg2 connections; if `conn=None` it creates and closes its own. Handles memoryview-to-bytes conversion for geometry data
- `walkability.py:miles_to_degrees()` is latitude-aware (accounts for Earth curvature)
- Buffer radius spatial queries use `ST_DWithin` against the PostGIS geometry column
- Geocoding uses tenacity for retries on transient failures

## Testing

Tests use `unittest.mock` throughout — no live database connection needed. Three test files:
- `tests/test_db.py` — env var validation, port parsing, connection factory, connection-closed detection
- `tests/test_walkability.py` — input validation, coordinate math, geocoding, data queries, map creation
- `tests/test_connection_caching.py` — connection lifecycle, cache clearing, closed connection recovery

## Configuration

- `PG*` env vars (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`) — required by all services and scripts
- `.streamlit/config.toml` — server runs headless on port 5000
- `.env` (gitignored) — environment variables for local/Replit
- Deployment target: Replit (autoscale)

## Workflow

See `agents/workflow-orchestration.md` for full details. Key points:

**Session management**: Work is tracked in `docs/sessions/`. Check `active/` for in-progress sessions, `backlog/` for planned work, `completed/` for prior art. Create or reuse a session file (`YYYY-MM-DD-[type]-[description].md`) with Objective, Success Criteria, and Progress Log. Keep at most 1-2 sessions active; move finished work to `completed/`.

**Lessons file**: `docs/dev_notes/lessons.md` contains corrective patterns learned from past mistakes. Review it at session start. After any bug fix or user correction, update it with a concrete do/don't rule so the failure category doesn't recur.

**Compounding fixes**: Every bug fix should also produce (1) a test that would have caught it and (2) a lessons entry. A fix without these is half-done.

**Plan mode**: Use plan mode for any non-trivial task (3+ steps or architectural decisions). If something goes wrong mid-task, stop and re-plan rather than pushing forward.

**Subagents**: Use subagents to keep the main context window clean — offload research, exploration, and parallel analysis. One focused task per subagent.

**Verification**: Never mark work complete without proving it works (run tests, check logs, demonstrate correctness).

## Cursor Rules

- `dev_log.mdc`: Dev notes use `YYYY_MM_DD_N.md` naming with Problem/Solution/Changes structure
- `streamlit.mdc` / `neondb.mdc`: Always reference latest Streamlit and NeonDB docs
