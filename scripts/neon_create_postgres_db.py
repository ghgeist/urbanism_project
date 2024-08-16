import logging
import psycopg2
import pandas as pd
import geopandas as gpd
from shapely import wkt
from sqlalchemy import create_engine
from tqdm import tqdm
import streamlit as st

# Configure logging to output to the terminal
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Get database connection details from Streamlit secrets
db_secrets = st.secrets["connections"]["postgresql"]
db_username = db_secrets["username"]
db_password = db_secrets["password"]
db_host = db_secrets["host"]
db_port = db_secrets["port"]
db_name = db_secrets["database"]

# Path to your CSV file
filepath = r'data\WalkabilityIndex\Natl_WI_simplified_drop_cols.csv'

try:
    logging.info("Loading DataFrame from CSV file...")
    # Load the DataFrame
    df = pd.read_csv(filepath)
    
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
    engine = create_engine(f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}')

    logging.info("Connecting to PostgreSQL database using psycopg2...")
    # Initialize connection to None
    connection = psycopg2.connect(
        user=db_username,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )
    cursor = connection.cursor()

    logging.info("Enabling PostGIS extension...")
    # Enable PostGIS extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
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
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()
        logging.info("PostgreSQL connection is closed")