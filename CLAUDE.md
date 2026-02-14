# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

React + FastAPI geospatial application that visualizes the EPA's National Walkability Index (NWI) dataset. Users search any U.S. address, ZIP code, or city, apply buffer and search radii, and view an interactive map (React-Leaflet) and summary at the Census block group level. The API serves geocoding and NWI summary endpoints; the React frontend is the primary UI.

## Tech Stack

- **Runtime**: Python 3.11+ (backend), Node.js (frontend)
- **Frontend**: React 19, Vite, React-Leaflet
- **API**: FastAPI, Uvicorn
- **Geospatial**: GeoPandas, Shapely, PyProj (backend); Leaflet (frontend)
- **Database**: PostgreSQL with PostGIS (Replit, Neon, or self-hosted)
- **Geocoding**: Nominatim via geopy (with tenacity retry logic)
- **DB drivers**: psycopg2-binary, SQLAlchemy

## Common Commands

```bash
# Run the API (from project root)
uvicorn api.main:app --reload

# Run the React frontend (from frontend/)
cd frontend && npm install && npm run dev

# Run all backend tests
pytest

# Run tests verbose
pytest -v

# Run Python lint checks
python -m ruff check api services scripts tests

# Run a specific test class
pytest tests/test_walkability.py::TestInputValidation

# Run with coverage
pytest --cov=services --cov-report=html

# Database setup (one-time, in order)
python scripts/enable_postgis.py
python scripts/create_neo_postgres_db.py
```

## Architecture

```
frontend/                 # React (Vite) — search, map, summary table
api/main.py               # FastAPI — health, geocode, NWI summary
services/
├── db.py                 # Framework-agnostic DB connection factory (env vars only)
└── walkability.py        # Geocoding, PostGIS queries, profile computation
```

**Request flow**: User enters address in React UI → frontend calls FastAPI `/geocode` and `/nwi/summary/by-query` → API uses `walkability.py` (Nominatim, PostGIS) → returns JSON → frontend renders map and table.

**Connection handling**: The API uses `services/db.py` for connections. Structured JSON debug logging is available via `WALKABILITY_DEBUG_LOG=1`.

**Database**: Single table `national_walkability_index` with columns: `geoid20` (PK), `d2a_ranked`, `d2b_ranked`, `d3b_ranked`, `d4a_ranked`, `natwalkind` (all NUMERIC(4,2)), and `geometry` (PostGIS GEOMETRY, SRID 4326). Loaded from `data/walkability_index_tabular.csv` (~203k rows).

## Key Implementation Details

- `db.py:get_db_connection()` reads `PG*` env vars exclusively. `validate_pg_env()` and `get_pg_env()` are reusable validators shared by scripts
- `walkability.py:get_walkability_data()` accepts psycopg2 connections; if `conn=None` it creates and closes its own. Handles memoryview-to-bytes conversion for geometry data
- `walkability.py:miles_to_degrees()` is latitude-aware (accounts for Earth curvature)
- Buffer radius spatial queries use `ST_DWithin` against the PostGIS geometry column
- Geocoding uses tenacity for retries on transient failures

## Testing

Tests use `unittest.mock` throughout — no live database connection needed. Two test files:
- `tests/test_db.py` — env var validation, port parsing, connection factory, connection-closed detection
- `tests/test_walkability.py` — input validation, coordinate math, geocoding, data queries, connection checks, map creation

When changing Python files, run `python -m ruff check api services scripts tests` and fix lint errors before marking work complete.

## Configuration

- `PG*` env vars (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`) — required by all services and scripts
- API default: http://127.0.0.1:8000; frontend dev server: http://localhost:5173
- `API_CORS_ORIGINS` — set in production to your frontend origin(s); defaults are localhost-only
- `WALKABILITY_DEBUG_LOG=1` — optional, dev only; do not set in production (can log request-related data)
- `.env` (gitignored) — environment variables for local/Replit
- **PIP_NO_INDEX**: If the environment has `PIP_NO_INDEX=1` (pip config `:env:.no-index='1'`), pip will not contact PyPI and installs will fail with "No matching distribution found." To install from PyPI for a session, unset the variable then install:
  ```powershell
  Remove-Item Env:PIP_NO_INDEX -ErrorAction SilentlyContinue
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ```
  Alternatively configure an explicit index URL if your environment requires a private/internal index.
- Deployment target: Replit (autoscale)
- **React frontend (Replit / SSH)**: On Replit, login shells load Node via `~/.bash_profile`. If you use SSH (e.g. Cursor) and `node`/`npm` are missing, reconnect to get a fresh login shell, or run `source /run/replit/env/latest`. See `frontend/README.md` for details.

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
- `neondb.mdc`: Reference latest NeonDB docs when touching database/config
