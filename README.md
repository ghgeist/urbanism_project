<p align="center">
  <img src="assets\header_image.jpg" alt="Exploring the National Walkability Index hero image">
</p>

# Exploring the National Walkability Index
Understand how walkable any U.S. neighborhood is by querying the EPA’s National Walkability Index and visualizing the results on an interactive Streamlit map.

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20Demo-ff4b4b?logo=streamlit&logoColor=white)](https://citybot.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/license/mit/)

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Quickstart](#quickstart)
5. [Usage](#usage)
6. [Deployment](#deployment)
7. [Data Pipeline](#data-pipeline)
8. [Testing & Validation](#testing--validation)
9. [Contributing & Roadmap](#contributing--roadmap)
10. [License](#license)

## Overview
The National Walkability Index (NWI) scores every U.S. census block group on a 1–20 scale across four dimensions: land-use mix, employment mix, street connectivity, and transit access. This project wraps the dataset in a geospatial API + Streamlit experience so planners, advocates, and curious residents can:

- Search an address, ZIP code, or city anywhere in the United States.
- Apply a buffer radius to explore nearby block groups.
- Inspect the component scores that make up the composite NWI value.

## Architecture
```
Streamlit UI (sidebar + map components)
        │
        ▼
Walkability service layer (`services/walkability.py`)
        │
        ▼
Neon PostgreSQL + PostGIS (national_walkability_index table)
```

- `app.py` boots Streamlit, renders the sidebar controls, and streams results.
- `components/sidebar.py` captures address/radius inputs and introduces the dataset.
- `components/map_display.py` calls cached data services, creates a Folium map, and surfaces a data table.
- `services/walkability.py` geocodes inputs with Nominatim, queries PostGIS via Streamlit’s SQL connection, and renders Folium layers.
- `scripts/create_neo_postgres_db.py` loads the processed CSV into Neon/PostGIS and maintains the spatial index.

## Tech Stack
| Area | Tools |
| --- | --- |
| Web UI | Streamlit, streamlit-folium |
| Geospatial | GeoPandas, Shapely, Folium, Tenacity |
| Data / Infra | Neon PostgreSQL with PostGIS, SQLAlchemy, psycopg2 |
| Tooling | Python 3.12, VS Code |

## Quickstart
### 1. Prerequisites
- Python 3.12+
- Git
- Access to a Neon PostgreSQL database with PostGIS enabled (free tier works)

### 2. Clone & install
```bash
git clone https://github.com/ghgeist/urbanism_project.git
cd urbanism_project
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Configure Streamlit secrets
Create `.streamlit/secrets.toml` with your Neon credentials (replace placeholders):
```toml
[connections.postgresql]
dialect = "postgresql"
host = "YOUR_NEON_HOST"
port = 5432
database = "YOUR_DB"
username = "YOUR_NEON_USER"
password = "YOUR_NEON_PASSWORD"
```

### 4. Load the walkability table (first-time setup)
The repository bundles a simplified CSV produced by `notebooks/compress_walkability_df.ipynb`. To seed the database locally, update the file path in `scripts/create_neo_postgres_db.py` if needed and run:
```bash
streamlit run scripts/create_neo_postgres_db.py
```
The script:
- Converts WKT polygons into geometries.
- Creates the `national_walkability_index` table.
- Loads ranked component scores plus geometries.
- Builds a GIST spatial index to accelerate `ST_DWithin` queries.

### 5. Run the app locally
```bash
streamlit run app.py
```

## Usage
- Enter any U.S. address, ZIP code, or city in the sidebar.
- Use the radius slider (0.1–10 miles) to control the buffer around the location.
- The map will draw block-group polygons colored by the National Walkability Index.
- The accompanying table lists component ranks (`d2a`, `d2b`, `d3b`, `d4a`) plus the composite score to support deeper analysis.

## Deployment
- **Streamlit Community Cloud:** Push your fork, configure the same `.streamlit/secrets.toml` via the Streamlit dashboard, and point the app to `app.py`.
- **Self-managed hosting:** Any container/service capable of running `streamlit run app.py` with access to Neon will work. Ensure HTTPS termination and secure handling of secrets.

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
- **Manual smoke test:** run `streamlit run app.py`, query “Knoxville, TN”, confirm polygons render and the data table populates.
- **Data sanity checks:** inspect `walkability.log` for geocoding errors and verify `national_walkability_index` counts in Postgres (`SELECT COUNT(*) ...`).
- Automated tests are not yet implemented; contributions that add unit tests (e.g., for geocoding retries or SQL generation) are welcome.

## Roadmap
- Enable GenAI/RAG queries across the walkability dataset.
- Add percentile comparisons versus metro/state averages.
- Cache frequently requested geometries to reduce query latency.

## License
[MIT License](https://opensource.org/license/mit/)
