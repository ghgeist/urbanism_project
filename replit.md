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
To populate the database (one-time setup), you need the EPA National Walkability Index dataset:
1. Download from: https://catalog.data.gov/dataset/walkability-index3
2. Process with `notebooks/compress_walkability_df.ipynb`
3. Load using `scripts/create_neo_postgres_db.py`

**Note:** Once the database is populated, the CSV file is no longer needed. The application queries PostgreSQL directly and does not use the CSV file during runtime.

## Configuration

### Database Setup (Replit PostgreSQL)

The app now supports Replit's built-in PostgreSQL database. Follow these steps:

1. **Enable PostgreSQL in Replit:**
   - Open the Secrets tab (🔒 icon in sidebar)
   - Replit will auto-generate PostgreSQL credentials
   - Environment variables will be automatically set:
     - `PGHOST`
     - `PGPORT`
     - `PGDATABASE`
     - `PGUSER`
     - `PGPASSWORD`

2. **Enable PostGIS extension:**
   ```bash
   python scripts/enable_postgis.py
   ```
   Or run via Streamlit:
   ```bash
   streamlit run scripts/enable_postgis.py
   ```

3. **Load the walkability data (one-time setup):**

   > **Note:** The CSV file is only needed for initial database setup. Once the database is populated, you can remove the CSV file and the `WALKABILITY_CSV_URL` environment variable. The running application queries PostgreSQL directly and does not use the CSV file.

   **Option A: Download from cloud storage (recommended for large files)**
   
   Upload `walkability_index_geospatial.csv` to cloud storage and get a direct HTTPS download link. Then:
   
   ```bash
   # Set the CSV URL as an environment variable in Replit Secrets
   # Key: WALKABILITY_CSV_URL
   # Value: https://your-cloud-storage-direct-download-link.csv
   
   # Then run the script
   streamlit run scripts/create_neo_postgres_db.py
   ```
   
   The script will automatically download the CSV and load it into the database. After successful setup, you can remove the CSV from cloud storage and delete the `WALKABILITY_CSV_URL` environment variable.
   
   **Option B: Use local file (if uploaded to Replit)**
   
   If you've already uploaded the CSV file to Replit:
   ```bash
   streamlit run scripts/create_neo_postgres_db.py
   ```
   
   The script defaults to `data/walkability_index_geospatial.csv` if no URL is provided. After successful setup, you can delete the local CSV file.

### Backward Compatibility

The app still supports Streamlit secrets configuration (`.streamlit/secrets.toml`) for local development or other hosting platforms. The code will automatically:
- Try Replit PostgreSQL environment variables first
- Fall back to Streamlit secrets if Replit env vars are not available
