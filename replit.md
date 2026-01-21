# Exploring the U.S. National Walkability Index

## Overview
This is a Streamlit application that visualizes the EPA's National Walkability Index (NWI) on an interactive map. Users can search for any U.S. address, ZIP code, or city and explore walkability scores for nearby census block groups.

## Project Structure
```
├── app.py                     # Main Streamlit application entry point
├── components/
│   ├── sidebar.py             # Sidebar with search inputs and info
│   └── map_display.py         # Map rendering and data display
├── services/
│   └── walkability.py         # Geocoding, database queries, map creation
├── scripts/
│   └── create_neo_postgres_db.py  # Database setup script
├── notebooks/                 # Jupyter notebooks for data processing
└── assets/                    # Images and static assets
```

## Tech Stack
- **Frontend**: Streamlit, streamlit-folium, Folium
- **Backend**: Python 3.11
- **Database**: PostgreSQL with PostGIS extension
- **Geospatial**: GeoPandas, Shapely, pyproj
- **Geocoding**: Geopy (Nominatim)

## Running the App
The app runs via Streamlit on port 5000:
```
streamlit run app.py --server.port=5000 --server.address=0.0.0.0 --server.headless=true
```

## Database Requirements
The app requires a PostgreSQL database with PostGIS extension and a `national_walkability_index` table containing walkability data. The table structure:
- geoid20: Census block group ID
- d2a_ranked, d2b_ranked, d3b_ranked, d4a_ranked: Component scores
- natwalkind: Composite walkability index (1-20)
- geometry: PostGIS geometry (EPSG:4326)

## Data Loading
To populate the database, you need the EPA National Walkability Index dataset:
1. Download from: https://catalog.data.gov/dataset/walkability-index3
2. Process with `notebooks/compress_walkability_df.ipynb`
3. Load using `scripts/create_neo_postgres_db.py`

## Configuration

### Database Setup (Replit PostgreSQL)

The app now supports Replit's built-in PostgreSQL database. Follow these steps:

1. **Enable PostgreSQL in Replit:**
   - Open the Secrets tab (🔒 icon in sidebar)
   - Replit will auto-generate PostgreSQL credentials
   - Environment variables will be automatically set:
     - `REPLIT_POSTGRES_HOST`
     - `REPLIT_POSTGRES_PORT`
     - `REPLIT_POSTGRES_DATABASE`
     - `REPLIT_POSTGRES_USER`
     - `REPLIT_POSTGRES_PASSWORD`

2. **Enable PostGIS extension:**
   ```bash
   python scripts/enable_postgis.py
   ```
   Or run via Streamlit:
   ```bash
   streamlit run scripts/enable_postgis.py
   ```

3. **Load the walkability data:**
   ```bash
   streamlit run scripts/create_neo_postgres_db.py
   ```

### Backward Compatibility

The app still supports Streamlit secrets configuration (`.streamlit/secrets.toml`) for local development or other hosting platforms. The code will automatically:
- Try Replit PostgreSQL environment variables first
- Fall back to Streamlit secrets if Replit env vars are not available
