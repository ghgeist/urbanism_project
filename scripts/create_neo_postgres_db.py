import logging
import psycopg2
import pandas as pd
import geopandas as gpd
from shapely import wkt
from sqlalchemy import create_engine
from tqdm import tqdm
import os
import urllib.request
import tempfile

# Configure logging to output to the terminal
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Get database connection details from Replit PostgreSQL environment variables
db_host = os.environ.get('PGHOST')
db_port = os.environ.get('PGPORT')
db_name = os.environ.get('PGDATABASE')
db_username = os.environ.get('PGUSER')
db_password = os.environ.get('PGPASSWORD')

if not all([db_host, db_port, db_name, db_username, db_password]):
    raise Exception("Could not find database credentials. Ensure Replit PostgreSQL is provisioned.")

# Get CSV source - can be URL or local file path
csv_source = os.environ.get('WALKABILITY_CSV_URL') or os.environ.get('WALKABILITY_CSV_PATH')
if not csv_source:
    # Default to local file
    csv_source = os.path.join('data', 'walkability_index_geospatial.csv')

try:
    # Initialize filepath to None for cleanup tracking
    filepath = None
    # Track whether we created a temporary file (not just if path is in temp dir)
    is_temp_file = False
    
    if csv_source.startswith('http://') or csv_source.startswith('https://'):
        # Download from URL
        logging.info(f"Downloading CSV from {csv_source}...")
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        filepath = tmp_file.name
        is_temp_file = True  # Mark that we created this temp file
        tmp_file.close()  # Close the file handle before downloading
        try:
            urllib.request.urlretrieve(csv_source, filepath)
            logging.info("CSV downloaded successfully.")
        except Exception as download_error:
            # Clean up temp file if download fails
            if filepath and os.path.exists(filepath):
                try:
                    os.unlink(filepath)
                except Exception:
                    pass
            raise download_error
    else:
        # Use local file
        filepath = csv_source
        logging.info(f"Using local CSV file: {filepath}")
    
    logging.info("Loading DataFrame from CSV file...")
    # Load the DataFrame
    df = pd.read_csv(filepath)
    logging.info(f"Loaded {len(df)} rows from CSV.")
    
    logging.info("Converting WKT geometries to geometries...")
    # Convert WKT geometries to geometries
    df['geometry'] = df['geometry'].apply(wkt.loads)
    
    logging.info("Creating GeoDataFrame...")
    # Create a GeoDataFrame with the initial CRS-> EPSG:4326
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    
    # Verify the CRS is set to EPSG:4326
    assert gdf.crs.to_string() == 'EPSG:4326', "CRS is not set to EPSG:4326"
    
    logging.info("Selecting specific columns...")
    # Select only the required columns -> Making a decision here based upon the database size limitations
    gdf = gdf[['geoid20',"d2a_ranked","d2b_ranked", "d3b_ranked", "d4a_ranked", 'natwalkind', 'geometry']]

    logging.info("Creating connection to PostgreSQL database...")
    # Create a connection to the PostgreSQL database
    db_port_int = int(db_port) if isinstance(db_port, str) else db_port
    engine = create_engine(f'postgresql://{db_username}:{db_password}@{db_host}:{db_port_int}/{db_name}')

    logging.info("Connecting to PostgreSQL database using psycopg2...")
    # Initialize connection to None
    connection = psycopg2.connect(
        user=db_username,
        password=db_password,
        host=db_host,
        port=int(db_port) if isinstance(db_port, str) else db_port,
        database=db_name
    )
    cursor = connection.cursor()

    logging.info("Enabling PostGIS extension...")
    # Enable PostGIS extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    connection.commit()

    logging.info("Dropping existing table if exists...")
    cursor.execute("DROP TABLE IF EXISTS national_walkability_index;")
    connection.commit()

    logging.info("Creating table with geometry column of type Geometry...")
    # Create table with geometry column of type Geometry
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS national_walkability_index (
                geoid20 VARCHAR(12) PRIMARY KEY,
                d2a_ranked NUMERIC(4, 2),
                d2b_ranked NUMERIC(4, 2),
                d3b_ranked NUMERIC(4, 2),
                d4a_ranked NUMERIC(4, 2),
                natwalkind NUMERIC(4, 2),
                geometry GEOMETRY(Geometry, 4326)
            );
        """)
    connection.commit()

    logging.info("Writing GeoDataFrame to PostgreSQL database...")
    # Write the GeoDataFrame to the PostgreSQL database with progress bar
    chunk_size = 1000
    total_chunks = (len(gdf) + chunk_size - 1) // chunk_size  # Correct chunk calculation
    with tqdm(total=total_chunks, desc="Writing to PostgreSQL", unit="chunk") as pbar:
        for i in range(total_chunks):
            chunk = gdf.iloc[i*chunk_size:(i+1)*chunk_size]
            chunk.to_postgis('national_walkability_index', engine, if_exists='append', index=False)
            pbar.update(1)

    logging.info("Creating spatial index on the 'geometry' column...")
    # Create spatial index on the 'geometry' column
    cursor.execute("CREATE INDEX IF NOT EXISTS geometry_idx ON national_walkability_index USING GIST (geometry);")
    connection.commit()

    logging.info("Script completed successfully.")

except Exception as e:
    logging.error("Error: %s", e)
    raise
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()
        logging.info("PostgreSQL connection is closed")
    # Clean up temporary file only if we created it (not if user provided a path in temp dir)
    if 'is_temp_file' in locals() and is_temp_file and 'filepath' in locals() and filepath is not None:
        try:
            os.unlink(filepath)
            logging.info("Temporary file cleaned up.")
        except Exception as cleanup_error:
            logging.warning(f"Could not clean up temporary file: {cleanup_error}")
