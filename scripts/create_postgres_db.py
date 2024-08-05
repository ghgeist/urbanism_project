import os
import logging
import psycopg2
import geopandas as gpd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

# Configure logging to output to the terminal
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Get database connection details from environment variables
db_username = os.getenv('DB_USERNAME')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Path to your geospatial file
filepath = r'data\WalkabilityIndex\Natl_WI.gdb'

try:
    logging.info("Loading GeoDataFrame from file...")
    # Load the GeoDataFrame
    gdf = gpd.read_file(filepath)
    
    logging.info("Converting CRS to EPSG:3857...")
    # Convert the lat/long CRS to EPSG:3857
    gdf = gdf.to_crs(epsg=3857)

    logging.info("Converting column names to lowercase...")
    # Convert all column names to lowercase
    gdf.columns = [col.lower() for col in gdf.columns]

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

    logging.info("Writing GeoDataFrame to PostgreSQL database...")
    # Write the GeoDataFrame to the PostgreSQL database with progress bar
    total_chunks = (len(gdf) // 1000) + 1
    with tqdm(total=total_chunks, desc="Writing to PostgreSQL", unit="chunk") as pbar:
        for i, chunk in enumerate(gdf.to_postgis('national_walkability_index', engine, if_exists='replace', chunksize=1000, method='multi', index=False)):
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